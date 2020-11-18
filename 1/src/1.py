from typing import List, Set
from itertools import product
from pathlib import Path

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
    score = {c: 0 for c in candidates}
    for profile in profiles:
        score[profile[0]] += 1
    max_score = max(score.values())
    return score, min(c for c in candidates if score[c] == max_score)  # Tie-breaking


def borda(candidates: Set[Candidate], profiles: List[Profile]):
    num_candidates = len(candidates)
    score = {c: 0 for c in candidates}
    for profile in profiles:
        for i, c in enumerate(profile):
            score[c] += num_candidates - i
    max_score = max(score.values())
    return score, min(c for c in candidates if score[c] == max_score)  # Tie-breaking


def nanson(candidates: Set[Candidate], profiles: List[Profile]):
    num_candidates = len(candidates)
    score = {c: 0 for c in candidates}
    for profile in profiles:
        for i, c in enumerate(profile):
            score[c] += num_candidates - i
    mean_score = sum(score.values()) / len(score)
    max_score = max(score.values())
    if mean_score == max_score:
        return [score], min([c for c in candidates if score[c] == max_score])  # Tie-breaking
    # Runoff with candidates that score above the mean score
    new_candidates = {c for c in candidates if score[c] > mean_score}
    new_profiles = [[c for c in p if c in new_candidates] for p in profiles]
    final_score, winner = nanson(new_candidates, new_profiles)
    all_scores = [{c: s for c, s in score.items()}]
    all_scores.extend(final_score)
    score.update(final_score[-1])
    return all_scores, winner


def stv(candidates: Set[Candidate], profiles: List[Profile]):
    vote_score = {c: 0 for c in candidates}
    vote_worth = 1  # Initially every voter has one vote
    all_scores = []
    score = {}
    while len(vote_score) > 1:
        for profile in profiles:
            vote_score[profile[0]] += vote_worth
        min_score = min(vote_score.values())
        max_score = max(vote_score.values())
        if min_score == max_score:
            break  # All candidates are equal
        min_candidate = min(vote_score, key=vote_score.get)
        # Remove the candidate with least score and redistribute it's score
        score[min_candidate] = len(score)
        del vote_score[min_candidate]
        profiles = [[c for c in p if c != min_candidate] for p in profiles]
        vote_worth = min_score / len(vote_score)
        all_scores.append({c: vote_score.get(c, 0) for c in candidates})
    score[next(iter(vote_score))] = len(score)
    return all_scores, min(vote_score)  # Tie-breaking


def copeland(candidates: Set[Candidate], profiles: List[Profile]):
    preferences = pairwise_preferences(candidates, profiles)
    score = {c: len([o for o in candidates if preferences[c, o]]) for c in candidates}
    max_score = max(score.values())
    return score, min(c for c in candidates if score[c] == max_score)  # Tie-breaking


def popularity(candidates: Set[Candidate], profiles: List[Profile]):
    borda_score, _ = borda(candidates, profiles)
    copeland_score, _ = copeland(candidates, profiles)
    score = {c: borda_score[c] * copeland_score[c] for c in candidates}
    max_score = max(score.values())
    return score, min(c for c in candidates if score[c] == max_score)  # Tie-breaking


def parse_agh(strict_order: Path):
    candidates: Set[Candidate] = set()
    profiles: List[Profile] = []
    with strict_order.open('r') as soc:
        data = soc.read().splitlines()
        num_candidates = int(data.pop(0))
        candidate_id = {}
        for i in range(num_candidates):
            cid, cname = data.pop(0).split(',')
            cid, cname = int(cid), cname.rstrip()
            candidate_id[cid] = cname
            candidates.add(cname)
        num_voters, num_rankings, num_unique_rankings = map(int, data.pop(0).split(','))
        for profile_data in data:
            profile = list(map(int, profile_data.split(',')))
            num_profiles = profile[0]
            profile = [candidate_id[cid] for cid in profile[1:]]
            for i in range(num_profiles):
                profiles.append(profile)
        print(f'Loaded {soc.name} with {num_candidates} candidates, {num_voters} voters, '
              f'{num_rankings} rankings and {num_unique_rankings} unique rankings')
    return candidates, profiles


def main():
    voting_rules = [plurality, borda, nanson, stv, copeland, popularity]
    agh = Path('../data/agh/')
    for soc in ('ED-00009-00000001.soc', 'ED-00009-00000002.soc'):
        candidates, profiles = parse_agh(agh / soc)
        print(f'Results for {soc}')
        condorcet = condorcet_winner(candidates, profiles)
        if condorcet:
            candidates.discard(condorcet)
            profiles = [[c for c in p if c != condorcet] for p in profiles]
            print(f'Condorcet winner {condorcet} discarded from candidates')
        if not candidates:
            print('No candidates left')
            continue
        print(f'{"Rule":12}{"Winner":10}Score')
        for rule in voting_rules:
            score, winner = rule(candidates, profiles)
            print(f'{rule.__name__:12}{winner:10}{score}')


if __name__ == '__main__':
    main()
