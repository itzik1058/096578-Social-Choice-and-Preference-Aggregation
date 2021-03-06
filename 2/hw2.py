import numpy as np
import pandas as pd
from itertools import combinations, product
import matplotlib.pyplot as plt


def argsort_random_break(x, axis=-1):  # Argsort x with random tie-breaking
    p = np.random.random(x.shape[axis])
    # Sort by x then by p
    return np.lexsort((p, x), axis)


def kendall_tau_distance(x, y):
    assert x.shape[0] == y.shape[0]
    n = x.shape[0]
    i, j = np.meshgrid(np.arange(n), np.arange(n))
    sx = np.argsort(x)
    sy = np.argsort(y)
    n_disordered = np.logical_or(np.logical_and(sx[i] < sx[j], sy[i] > sy[j]),
                                 np.logical_and(sx[i] > sx[j], sy[i] < sy[j]))
    return n_disordered.sum() / (n * (n - 1))


def proxy_truth_discovery(votes, rule):
    n_voters = votes.shape[0]
    distance = np.empty(shape=(n_voters, n_voters))
    for v1, v2 in product(range(n_voters), repeat=2):
        distance[v1, v2] = kendall_tau_distance(votes[v1], votes[v2])
    pi = (np.sum(distance, axis=1) - np.diag(distance)) / (n_voters - 1)
    fault = pi
    weights = 0.5 - fault
    return rule(votes, weights), fault


def distance_truth_discovery(votes, rule):
    n_voters = votes.shape[0]
    y = rule(votes)
    distance = np.empty(n_voters)
    for v in range(n_voters):
        distance[v] = kendall_tau_distance(y, votes[v])
    fault = distance
    weights = 0.5 - fault
    return rule(votes, weights), fault


def unweighted(votes, rule):
    return rule(votes), None


def grofman_truth_discovery(votes, rule):
    n_voters = votes.shape[0]
    distance = np.empty(shape=(n_voters, n_voters))
    for v1, v2 in product(range(n_voters), repeat=2):
        distance[v1, v2] = kendall_tau_distance(votes[v1], votes[v2])
    pi = (np.sum(distance, axis=1) - np.diag(distance)) / (n_voters - 1)
    pi = pi * (1 - 1e-8) + 1e-8  # Make sure pi is not 0 or 1
    weights = np.log(1 - pi) - np.log(pi)
    return rule(votes, weights)


def weighted_borda(votes, weights=None):
    n_voters, n_candidates = votes.shape
    if weights is None:
        weights = np.ones(n_voters)
    scores = n_candidates - 1 - np.argsort(votes)
    return argsort_random_break(-weights @ scores)  # Sort descending


def weighted_copeland(votes, weights=None):
    n_voters, n_candidates = votes.shape
    if weights is None:
        weights = np.ones(n_voters)
    pairwise = np.empty(shape=(n_candidates, n_candidates))
    for c1, c2 in combinations(range(n_candidates), 2):
        first, second = min(c1, c2), max(c1, c2)
        pairwise[votes[:, first], votes[:, second]] += weights
        pairwise[votes[:, second], votes[:, first]] -= weights
    scores = -np.sum(pairwise > 0, axis=1)
    return argsort_random_break(scores)  # Sort descending


def plot_proxy_truth_distance(votes, true_ranking):
    n_voters = votes.shape[0]
    distance = np.empty(shape=(n_voters, n_voters))
    for v1, v2 in product(range(n_voters), repeat=2):
        distance[v1, v2] = kendall_tau_distance(votes[v1], votes[v2])
    pi = (np.sum(distance, axis=1) - np.diag(distance)) / (n_voters - 1)
    truth_distance = np.empty(n_voters)
    for v in range(n_voters):
        truth_distance[v] = kendall_tau_distance(true_ranking, votes[v])
    plt.xlabel('Distance from truth')
    plt.ylabel('Proxy distance')
    plt.scatter(truth_distance, pi)
    plt.show()


def plot_average_error(votes, true_ranking, n_iter=500):
    plt.figure(figsize=(10, 7))
    for p, (rule, name) in enumerate([(weighted_borda, 'Borda'), (weighted_copeland, 'Copeland')]):
        plt.subplot(2, 1, p + 1)
        voters = np.arange(85)
        sample_size = np.arange(5, 90, 5)
        average_true_error = np.empty(shape=(4, sample_size.shape[0]))
        for i, size in enumerate(sample_size):
            print(f'{rule.__name__} with sample size {size}')
            for _ in range(n_iter):
                sample_votes = votes[np.random.choice(voters, size)]
                for m, method in enumerate([proxy_truth_discovery, distance_truth_discovery, unweighted]):
                    average_true_error[m, i] += kendall_tau_distance(true_ranking, method(sample_votes, rule)[0])
                grofman_truth = grofman_truth_discovery(sample_votes, weighted_borda)
                average_true_error[3, i] += kendall_tau_distance(true_ranking, grofman_truth)
            average_true_error[:, i] /= n_iter
        plt.plot(sample_size, average_true_error[0], label='Proxy Truth Discovery')
        plt.plot(sample_size, average_true_error[1], label='Distance Truth Discovery')
        plt.plot(sample_size, average_true_error[2], label='Unweighted')
        plt.plot(sample_size, average_true_error[3], label='Grofman Truth Discovery with Borda')
        plt.xlabel('Sample size')
        plt.ylabel('Average true distance')
        plt.title(name)
        plt.legend()
    plt.subplots_adjust()
    plt.show()


def main():
    votes = pd.read_csv('voters.csv', header=None).to_numpy(dtype=np.int)
    truth = pd.read_csv('truth.csv', header=None).to_numpy(dtype=np.int)
    results = []
    for method in (proxy_truth_discovery, distance_truth_discovery, unweighted):
        for rule in (weighted_borda, weighted_copeland):
            results.append(method(votes, rule)[0])
    results.append(grofman_truth_discovery(votes, weighted_borda))
    pd.DataFrame(results).to_csv('estimations.csv', header=False, index=False)
    truth_candidates, truth_ranking = truth
    truth_ranking = truth_candidates[truth_ranking]
    # Keep only relevant votes
    truth_votes = votes[np.isin(votes, truth_ranking)].reshape(votes.shape[0], truth_ranking.shape[0])
    # Map remaining candidates into a smaller range
    truth_ranking_mapped = np.digitize(truth_ranking.ravel(), np.sort(truth_ranking), right=True)
    truth_votes_mapped = np.digitize(truth_votes.ravel(), np.sort(truth_ranking), right=True).reshape(truth_votes.shape)
    # Plots:
    # plot_proxy_truth_distance(truth_votes_mapped, truth_ranking_mapped)
    # plot_average_error(truth_votes_mapped, truth_ranking_mapped)


if __name__ == '__main__':
    main()
