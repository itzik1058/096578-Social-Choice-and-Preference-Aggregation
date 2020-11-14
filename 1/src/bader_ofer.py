data_file = open("votes.csv", "r")
data_lines = data_file.readlines()

odafim_pairs_file = open("agreements.csv", "r")
odafim_pair_lines = odafim_pairs_file.readlines()

PARLIAMENT_SIZE = 120


def threshold(election):
    """
    Given the election number, returns the voting threshold implemented in that election.
    """
    if election <= 12:
        return 1 / 100
    elif election <= 16:
        return 1.5 / 100
    elif election <= 19:
        return 2 / 100
    else:
        return 3.25 / 100


def bader_ofer(election, data, odafim_pairs):
    """
    election - an integer of the election number
    data - a dictionary mapping party name to number of votes it received in the election
    odafim_pairs - a dictionary mapping every party to a tuple of (id of the odafim agreements, other party),
                    and also mapping the id of the odafim agreements to (party1, party2) of the agreement.

    return - a dictionary mapping every party in data to the mandates it should receive.
    """
    num_votes = sum(data.values())
    mandate_cost = num_votes / PARLIAMENT_SIZE
    party_votes = {p: v for p, v in data.items() if v > num_votes * threshold(election)}
    party_mandates = {p: int(v / mandate_cost) for p, v in party_votes.items()}
    leftover_mandates = PARLIAMENT_SIZE - sum(party_mandates.values())
    grouped_votes = {}
    grouped_mandates = {}
    for p in party_votes:
        if p in odafim_pairs:
            pair_id, pair_party = odafim_pairs[p]
            grouped_votes[pair_id] = party_votes[p] + party_votes[pair_party]
            grouped_mandates[pair_id] = party_mandates[p] + party_mandates[pair_party]
        else:
            grouped_votes[p] = party_votes[p]
            grouped_mandates[p] = party_mandates[p]
    for i in range(leftover_mandates):
        grouped_worth = {p: v / (grouped_mandates[p] + 1) for p, v in grouped_votes.items()}
        winner = max(grouped_worth, key=grouped_worth.get)
        party_winner = winner
        if winner in odafim_pairs:
            party_worth = {p: party_votes[p] / (party_mandates[p] + 1) for p in odafim_pairs[winner]}
            party_winner = max(odafim_pairs[winner], key=party_worth.get)
        grouped_mandates[winner] += 1
        party_mandates[party_winner] += 1
    return party_mandates


elections = {}
election_results = {}
odafim_pairs = {}

running_id = 0

for line in odafim_pair_lines[1:]:
    election, party1, party2 = line.split(",")
    election = int(election)
    party2 = party2.strip()
    if election not in odafim_pairs:
        odafim_pairs[election] = {}

    odafim_pairs[election][party1] = [running_id, party2]
    odafim_pairs[election][party2] = [running_id, party1]
    odafim_pairs[election][running_id] = [party1, party2]
    running_id += 1

for line in data_lines[1:]:
    election, party, mandates, votes = line.split(",")
    party = party.strip()
    votes = int(votes)
    mandates = int(mandates)
    election = int(election)
    if election not in elections:
        elections[election] = {}
        election_results[election] = {}
    elections[election][party] = votes
    election_results[election][party] = mandates

for election in elections:
    data = elections[election]
    predictions = bader_ofer(election, data, odafim_pairs[election])
    if predictions != election_results[election]:
        print(
            "Error in election {}, predicted: {}, actual: {}".format(election, predictions, election_results[election]))

print("Success! All elections 17-23 predicted correctly")
