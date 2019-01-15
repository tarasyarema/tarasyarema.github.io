import numpy as np

def pagerank(M, eps = 1.0e-8, d = 0.85):
    # Get number of vertices of the graph
    N = M.shape[1]
    
    # Generate random array of dimension N and normalize it
    v = np.random.rand(N, 1)
    v = v / np.linalg.norm(v, 1)
    
    # Init score matrix
    last_v = np.ones((N, 1))
    
    # Secured convergence formula
    M_hat = ((1 - d) / N) * np.ones(M.shape) + d * M
    
    # Init step counter
    steps = 1
    
    # Loop while the norm of two steps is greater than eps
    while np.linalg.norm(v - last_v, 2) > eps:
        last_v = v
        v = np.matmul(M_hat, v)
        
        steps += 1
       
    print('Steps: {}'.format(steps))
    print('Site #{} is the best with score {}'.format(np.argmax(v), np.max(v)))

sites_matrix = np.array(
    [[0, 0, 0, 0, 1],
     [0.5, 0, 0, 0, 0],
     [0.5, 0, 0, 0, 0],
     [0, 1, 0.5, 0, 0],
     [0, 0, 0.5, 1, 0]]
)

pagerank(sites_matrix)
