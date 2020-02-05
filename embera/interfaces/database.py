import os
import json
import time
import dimod
import numpy

from json import load as _load
from json import dump as _dump

from embera.interfaces.embedding import Embedding
from embera.interfaces.json import EmberaEncoder, EmberaDecoder

from dimod.serialization.json import DimodEncoder, DimodDecoder

from dwave.embedding import unembed_sampleset

from networkx import Graph
from networkx.readwrite.json_graph import node_link_data as _serialize_graph
from networkx.readwrite.json_graph import node_link_graph as _deserialize_graph

__all__ = ["EmberaDataBase"]


class EmberaDataBase:
    """ DataBase class to store bqms, embeddings, and samplesets. """
    path = None
    aliases = {}

    def __init__(self, path="./EmberaDB/"):

        self.path = path
        if not os.path.isdir(self.path):
            os.mkdir(self.path)

        self.bqms_path = os.path.join(self.path,'bqms')
        if not os.path.isdir(self.bqms_path):
            os.mkdir(self.bqms_path)

        self.embeddings_path = os.path.join(self.path,'embeddings')
        if not os.path.isdir(self.embeddings_path):
            os.mkdir(self.embeddings_path)

        self.samplesets_path =  os.path.join(self.path,'samplesets')
        if not os.path.isdir(self.samplesets_path):
            os.mkdir(self.samplesets_path)

        self.aliases_path = os.path.join(self.path,'aliases.json')
        if os.path.exists(self.aliases_path):
            with open(self.aliases_path,'r') as fp:
                self.aliases = _load(fp)

    def timestamp(self):
        return f"{time.time():.0f}"

    def update_aliases(self):
        with open(self.aliases_path,'w+') as fp:
            _dump(self.aliases,fp)

    def set_bqm_alias(self, bqm, alias):
        id = self.id_bqm(bqm)
        bqm_aliases = self.aliases.get('bqm',{})
        bqm_aliases[alias] = id
        self.aliases['bqm'] = bqm_aliases
        self.update_aliases()

    def set_source_alias(self, source, alias):
        id = self.id_source(source)
        source_aliases = self.aliases.get('source',{})
        source_aliases[alias] = id
        self.aliases['source'] = source_aliases
        self.update_aliases()

    def set_target_alias(self, target, alias):
        id = self.id_target(target)
        target_aliases = self.aliases.get('target',{})
        target_aliases[alias] = id
        self.aliases['target'] = target_aliases
        self.update_aliases()

    def set_embedding_alias(self, embedding, alias):
        assert(isinstance(embedding,Embedding))
        id = self.id_embedding(embedding)
        embedding_aliases = self.aliases.get('embedding',{})
        embedding_aliases[alias] = id
        self.aliases['embedding'] = embedding_aliases
        self.update_aliases()

    def id_bqm(self, bqm):
        if isinstance(bqm,dimod.BinaryQuadraticModel):
            lin_key = sum(bqm.linear.values())
            quad_key = sum(bqm.quadratic.values())
            id = f"{lin_key:f}_{quad_key:f}".replace('.','').replace('-','')
        elif isinstance(bqm,Graph):
            lin_key = sum([data['bias'] for v,data in bqm.nodes(data=True)])
            quad_key = sum([data['bias'] for u,v,data in bqm.edges(data=True)])
            id = f"{lin_key:f}_{quad_key:f}".replace('.','').replace('-','')
            if bqm.name: self.set_bqm_alias(id,bqm.name)
        elif isinstance(bqm,str):
            id = self.aliases.get('bqm',{}).get(bqm,bqm)
        else:
            raise ValueError("BQM must be dimod.BinaryQuadraticModel, networkx.Graph, or str")
        return id

    def __graph_key(self, graph):
        if isinstance(graph, Graph):
            degree = graph.degree()
        else:
            if isinstance(graph, dimod.BinaryQuadraticModel):
                edgelist = graph.quadratic
            else:
                edgelist = graph
            degree_dict = {}
            for u,v in edgelist:
                degree_dict[u] = 1 + degree_dict.get(u,0)
                degree_dict[v] = 1 + degree_dict.get(v,0)
            degree = degree_dict.items()
        degree_hist = {}
        for v,d in degree:
            degree_hist[d] = 1+degree_hist.get(d,0)

        return (c for bin in sorted(degree_hist.items(), reverse=True) for c in bin)

    def id_source(self, source):
        if isinstance(source,str):
            id = self.aliases.get('source',{}).get(source,source)
        elif isinstance(source,(dimod.BinaryQuadraticModel,Graph,list)):
            id = "".join([str(v) for v in self.__graph_key(source)])
        else:
            raise ValueError("Source must be dimod.BinaryQuadraticModel, networkx.Graph, list of tuples or str")

        if hasattr(source,'name'): self.set_source_alias(id,source.name)
        return id

    def id_target(self, target):
        if isinstance(target,str):
            id = self.aliases.get('target',{}).get(target,target)
        elif isinstance(target,(dimod.BinaryQuadraticModel,Graph,list)):
            id = "".join([str(v) for v in self.__graph_key(target)])
        else:
            raise ValueError("Target must be networkx.Graph, list of tuples or str")

        if hasattr(target,'name'): self.set_target_alias(id,target.name)
        return id

    def id_embedding(self, embedding):
        if isinstance(embedding,Embedding):
            id = embedding.id
        elif isinstance(embedding,dict):
            id = Embedding(embedding).id
        elif isinstance(embedding,str):
            id = self.aliases.get('embedding',{}).get(embedding,embedding)
        else:
            raise ValueError("Embedding must be embera.Embedding, dict, or str")
        return id

    def get_path(self, dir_path, filename=None):
        path = ""
        for dir in dir_path:
            path = os.path.join(path,dir)
            if not os.path.isdir(path):
                os.mkdir(path)
        if filename is not None:
            path = os.path.join(path,filename+'.json')
        return path

    """ ######################## BinaryQuadraticModels ##################### """
    def load_bqms(self, source, tags=[]):
        source_id = self.id_source(source)

        bqms_path = os.path.join(self.bqms_path,source_id)

        bqms = []
        for root, dirs, files in os.walk(bqms_path):
            root_dirs = os.path.normpath(root).split(os.path.sep)
            if all(tag in root_dirs for tag in tags):
                for file in files:
                    bqm_path = os.path.join(root,file)
                    with open(bqm_path,'r') as fp:
                        bqm = _load(fp,cls=DimodDecoder)
                    bqms.append(bqm)

        return bqms

    def load_bqm(self, source, tags=[], index=0):
        bqms = self.load_bqms(source,tags)
        return bqms.pop(index)

    def dump_bqm(self, bqm, tags=[]):
        source_id = self.id_source(bqm)
        bqm_id = self.id_bqm(bqm)
        bqms_path = [self.bqms_path,source_id]+tags

        bqm_path = self.get_path(bqms_path, bqm_id)

        with open(bqm_path,'w+') as fp:
            bqm_ser = bqm.to_serializable(bias_dtype=numpy.float64)
            json.dump(bqm_ser,fp)

    def dump_ising(self, h, J, tags=[]):
        bqm = dimod.BinaryQuadraticModel(h,J,0.0,'SPIN',tags=tags)
        self.dump_bqm(bqm,tags)

    """ ############################# SampleSets ########################### """
    def load_samplesets(self, bqm, target, embedding="", tags=[], unembed_args={}):
        source_id = self.id_source(bqm)
        bqm_id = self.id_bqm(bqm)
        target_id = self.id_target(target)
        embedding_id = self.id_embedding(embedding)

        dir_path = [self.samplesets_path,source_id,bqm_id,target_id,embedding_id]
        samplesets_path = os.path.join(*dir_path)

        samplesets = []
        for root, dirs, files in os.walk(samplesets_path):
            root_dirs = os.path.normpath(root).split(os.path.sep)
            if all(tag in root_dirs for tag in tags):
                for file in files:
                    sampleset_path = os.path.join(root,file)
                    with open(sampleset_path,'r') as fp:
                        sampleset = _load(fp,cls=DimodDecoder)
                    samplesets.append(sampleset)

        if embedding:
            return [unembed_sampleset(s,embedding,bqm,**unembed_args) for s in samplesets]
        else:
            return samplesets

    def load_sampleset(self, bqm, target, embedding="", tags=[], unembed_args={}):
        """ Load a sampleset object from JSON format, filed under:
            <EmberaDB>/<bqm_id>/<target_id>/<tag>/<embedding_id>.json
            If tag and/or embedding are not provided, returns the concatenation
            of all samples found under the given criteria.

        Arguments:

            target: (str)


        Optional Arguments:
            If none of the optional arguments are given, all samplesets under
            that path are concatenated.

            tag: (str, default="")
                If provided, sampleset is read from directory ./<tag>/

            embedding: (embera.Embedding, dict, or str, default=None)
                Dictionary is converted to Embedding, Embedding ID is used.
                String is taken literally as path.
                If "", concatenate all under <EmberaDB>/<bqm_id>/<target_id>/<tag>
                If {}, return `native` sampleset. i.e. <Embedding({}).id>.json

        """
        samplesets = self.load_samplesets(bqm,target,embedding,tags,unembed_args)


        if not samplesets:
            raise ValueError("No samplesets found.")
        else:
            sampleset = dimod.concatenate(samplesets)
            for s in samplesets: sampleset.info.update(s.info)
            return sampleset

    def dump_sampleset(self, bqm, target, embedding, sampleset, tags=[]):
        source_id = self.id_source(bqm)
        bqm_id = self.id_bqm(bqm)
        target_id = self.id_target(target)
        embedding_id = self.id_embedding(embedding)

        samplesets_path = [self.samplesets_path,source_id,bqm_id,target_id,embedding_id]+tags

        sampleset_filename = f"{self.timestamp()}_{len(sampleset)}"
        sampleset_path = self.get_path(samplesets_path, sampleset_filename)

        with open(sampleset_path,'w+') as fp:
            _dump(sampleset,fp,cls=DimodEncoder)

    """ ############################ Embeddings ############################ """
    def load_embeddings(self, source, target, tags=[]):
        source_id = self.id_source(source)
        target_id = self.id_target(target)

        embeddings_path = os.path.join(self.embeddings_path,source_id,target_id)

        embedding_filenames = []
        for root, dirs, files in os.walk(embeddings_path):
            root_dirs = os.path.normpath(root).split(os.path.sep)
            if all(tag in root_dirs for tag in tags):
                for file in files:
                    embedding_filenames.append((root,file))

        embeddings = []
        if not embedding_filenames: return embeddings

        embedding_filenames.sort(key=lambda entry: entry[1])

        for embedding_filename in embedding_filenames:
            embedding_path = os.path.join(*embedding_filename)

            with open(embedding_path,'r') as fp:
                embedding = _load(fp,cls=EmberaDecoder)
            embeddings.append(embedding)

        return embeddings

    def load_embedding(self, source, target, tags=[], index=0):
        """ Load an embedding object from JSON format, filed under:
            <EmberaDB>/<source_id>/<target_id>/<embedding_id>.json
            or, if tag is provided:
            <EmberaDB>/<source_id>/<target_id>/<tag>/<embedding_id>.json

            Arguments:
                source: (dimod.BinaryQuadraticModel, networkx.Graph w/ biases, list of tuples, or str)
                    BQM, Graph, and list of edge tuples are hashed.
                    String is taken literally as path.
                target: (list of tuples, networkx.Graph, or str)
                    List and Graph are hashed. String is taken literally as path.

            Optional Arguments:
                tag: (str, default="")
                    If provided, embedding is read from directory ./<tag>/
                index: (int, default=0)
                    Embeddings are stored sorted by `quality_key`. Therefore,
                    `index==0` is the "best" embedding found for that bqm, onto
                    that target, with that `tag`.

            Returns:
                embedding: (embera.Embedding)
                    Embedding at given rank or empty dictionary if none found.

        """
        embeddings = self.load_embeddings(source,target,tags)
        return  embeddings.pop(index)


    def dump_embedding(self, source, target, embedding, tags=[]):
        """ Store an embedding object in JSON format, filed under:
            <EmberaDB>/<source_id>/<target_id>/<embedding_id>.json
            or, if tag is provided:
            <EmberaDB>/<source_id>/<target_id>/<tag>/<embedding_id>.json

            Arguments:
                source: (dimod.BinaryQuadraticModel, networkx.Graph w/ biases, list of tuples, or str)
                    BQM, Graph, and list of edge tuples are hashed.
                    String is taken literally as path.

                target: (list of edge tuples, networkx.Graph, or str)
                    List and Graph are hashed. String is taken literally as path.

                embedding: (embera.Embedding, dict, or str)
                    List is converted to Embedding, Embedding ID is used.
                    String is taken literally as path.

            Optional Arguments:
                tag: (str, default="")
                    If provided, embedding is stored under a directory ./<tag>/
                    Useful to identify method used for embedding.
        """
        source_id = self.id_source(source)
        target_id = self.id_target(target)
        embeddings_path = [self.embeddings_path,source_id,target_id] + tags

        if isinstance(embedding,Embedding): embedding_obj = embedding
        else: embedding_obj = Embedding(embedding)

        embedding_path = self.get_path(embeddings_path, embedding_obj.id)

        with open(embedding_path,'w+') as fp:
            _dump(embedding_obj,fp,cls=EmberaEncoder)
