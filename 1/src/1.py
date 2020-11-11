from typing import List, Set
from itertools import product

Candidate = str
Profile = List[Candidate]


def pairwise_preferences(candidates: Set[Candidate], profiles: List[Profile]):
    score = {candidate_pair: 0 for candidate_pair in product(candidates, repeat=2)}
    for profile in profiles:
        for i, candidate in enumerate(profile):
            for c in profile[i + 1:]:
                score[(candidate, c)] += 1
                score[(c, candidate)] -= 1
    preferences = {candidate_pair: score > 0 for candidate_pair, score in score.items()}
    return preferences


def condorcet_winner(candidates: Set[Candidate], profiles: List[Profile]):
    preferences = pairwise_preferences(candidates, profiles)
    for candidate in candidates:
        if all(preferences[candidate, c] for c in candidates if c != candidate):
            return candidate
    return None


def plurality(candidates: Set[Candidate], profiles: List[Profile]):
    condorcet = condorcet_winner(candidates, profiles)
    if condorcet:
        return condorcet
    score = {c: 0 for c in candidates}
    for profile in profiles:
        score[profile[0]] += 1
    max_score = max(score.values())
    return min(c for c in candidates if score[c] == max_score)  # Tie-breaking


def borda(candidates: Set[Candidate], profiles: List[Profile]):
    condorcet = condorcet_winner(candidates, profiles)
    if condorcet:
        return condorcet
    num_candidates = len(candidates)
    score = {c: 0 for c in candidates}
    for i, profile in enumerate(profiles):
        score[profile[0]] += num_candidates - i
    max_score = max(score.values())
    return min(c for c in candidates if score[c] == max_score)  # Tie-breaking


def nanson(candidates: Set[Candidate], profiles: List[Profile]):
    condorcet = condorcet_winner(candidates, profiles)
    if condorcet:
        return condorcet
    num_candidates = len(candidates)
    score = {c: 0 for c in candidates}
    for i, profile in enumerate(profiles):
        score[profile[0]] += num_candidates - i
    mean_score = sum(score.values()) / len(score)
    max_score = max(score.values())
    if mean_score == max_score:
        return min([c for c in candidates if score[c] == max_score])  # Tie-breaking
    # Runoff with candidates that score above the mean score
    new_candidates = {c for c in candidates if score[c] > mean_score}
    new_profiles = [[c for c in p if c in new_candidates] for p in profiles]
    return nanson(new_candidates, new_profiles)


def stv(candidates: Set[Candidate], profiles: List[Profile]):
    condorcet = condorcet_winner(candidates, profiles)
    if condorcet:
        return condorcet
    score = {c: 0 for c in candidates}
    vote_score = 1  # Initially every voter has one vote
    while len(score) > 1:
        for profile in profiles:
            score[profile[0]] += vote_score
        min_score = min(score.values())
        max_score = max(score.values())
        if min_score == max_score:
            break  # All candidates are equal
        min_candidate = min(score, key=score.get)
        # Remove the candidate with least score and redistribute it's score
        del score[min_candidate]
        profiles = [[c for c in p if c != min_candidate] for p in profiles]
        vote_score = min_score / len(score)
    return min(score)  # Tie-breaking


def copeland(candidates: Set[Candidate], profiles: List[Profile]):
    condorcet = condorcet_winner(candidates, profiles)
    if condorcet:
        return condorcet
    preferences = pairwise_preferences(candidates, profiles)
    score = {c: len([o for o in candidates if preferences[c, o]]) for c in candidates}
    max_score = max(score.values())
    return min(c for c in candidates if score[c] == max_score)  # Tie-breaking


def main():
    voting_rules = [plurality, borda, nanson, stv, copeland]
    candidates = {'A', 'B', 'C', 'D'}
    profiles = [
        ['A', 'C', 'B', 'D'],
        ['D', 'A', 'B', 'C'],
        ['D', 'A', 'C', 'B'],
        ['C', 'A', 'D', 'B']
    ]
    condorcet = condorcet_winner(candidates, profiles)
    print(f'Condercet winner: {condorcet}')
    print(f'{"Rule":10}Winner')
    for rule in voting_rules:
        print(f'{rule.__name__:10}{rule(candidates, profiles)}')


if __name__ == '__main__':
    main()
