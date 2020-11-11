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
    return "IMPLEMENT ME"


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
