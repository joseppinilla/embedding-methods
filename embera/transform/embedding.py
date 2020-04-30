import dwave
import minorminer
import networkx as nx
import dwave_networkx as dnx

from embera.utilities.decorators import nx_graph, dnx_graph, dnx_graph_embedding
from embera.preprocess.tiling_parser import DWaveNetworkXTiling

@nx_graph(0)
@dnx_graph(1)
@dnx_graph_embedding(1,2)
def sliding_window(S, T, embedding):
    """ TODO: Using a sling window approach, transform the embedding from one region
        of the Chimera graph to another. This is useful when an embedding is
        done for a D-Wave machine and it's necessary to find an identical
        embedding on another D-Wave machine with different yield.

        Algorithm:
            1) Parse embedding and target graph to find margins.
            2) Move qubit to window i and check if nodes are available
            3) If all nodes are available, go to 4, else go to 3
            4) Check if edges are available, if not, return to 2.

        Args:
            S (:obj:`networkx.Graph`):

            T (:obj:`networkx.Graph`):

            embedding (dict/:obj:`embera.Embedding`):

        Returns:
            embedding:
    """

    T_tiling = DWaveNetworkXTiling(T)

    width = 0
    height = 0
    x_offset = 0
    y_offset = 0
    for v,chain in embedding.items():
        for q in chain:
            (t,i,j) = T_tiling.get_tile(q)



    return embedding

@nx_graph(0)
@dnx_graph(1)
@dnx_graph_embedding(1,2)
def rotate(S, T, embedding):
    """ Rotate the embedding on the same graph to re-distribute qubit
        assignments. If a perfect fit isn't found, due to disabled qubits,
        a minor-embedding heuristic is used in a "relaxed" way to find a valid
        assignment.
    """
    for v, chain in embedding.items():
        pass


    return embedding

@nx_graph(0)
@dnx_graph(1)
@dnx_graph_embedding(1,2)
def spread_out(S, T, embedding):
    """ TODO: Alter the embedding to add qubit chains by moving qubit
        assignments onto qubit in tiles farther from the center of the device
        graph.
            1) Use Chimera/Pegasus index to determine tile of each node
            2) Transform the tile assignment to spread out the embedding
            3) Assign nodes to corresponding qubit in new tiles
            4) Perform an "embedding pass" or path search to reconnect all nodes
    """
    T_tiling = DWaveNetworkXTiling(T)


    origin = T_tiling.shape
    end = (0,)*len(origin)
    for v,chain in embedding.items():
        for q in chain:
            tile = T_tiling.get_tile(q)
            if tile < origin:
                origin = tile
            if tile > end:
                end = tile

    return embedding



@nx_graph(0)
@dnx_graph(1)
@dnx_graph_embedding(1,2)
def lp_chain_reduce(S, T, embedding):
    """ TODO: Use a linear programming formulation to resolve shorter chains
        from a given embedding.
            1) Turn chains into shared qubits
            2) Create LP formulation
            3) Resolve chains
    """
    return embedding
