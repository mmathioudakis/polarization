"""
a script to measure polarized networks
"""
import sys, os
import polarlib.file_utils as file_utils
import polarlib.polar_utils as polar_utils
import argparse
import json
import re


if __name__ == '__main__' :

	# parse arguments

	parser = argparse.ArgumentParser()
	parser.add_argument('kind', choices = ['retweets', 'replies'],
		default = 'retweets',
		help = 'What kind of networks to analyze.')
	parser.add_argument('topic', help = 'keyword defining the topic')
	parser.add_argument('granularity', choices = ['week', 'month'],
		help = 'Granularity.')
	parser.add_argument('--klcc', action = 'store_true', default = False,
		help = 'Work with largest connected component.')
	parser.add_argument('-a', '--alpha', type = float, default = 0.10,
		help = 'Top ties fraction.')
	parser.add_argument('-o', '--output_folder',
		default = 'stressed_polarization/results',
		help = 'Folder where to store results.')


	args = parser.parse_args()


	# this is where we store all the results
	results = {'settings': {'granularity': args.granularity, 'topic': args.topic,
			'alpha': args.alpha}, 'measures': {}}

	# go over networks
	ALL_RT_NETWORKS_FOLDER = 'data/twitter_under_stress/networks'
	ALL_MT_NETWORKS_FOLDER = 'data/twitter_under_stress/reply_networks'

	ALL_NETWORKS_FOLDER = ALL_MT_NETWORKS_FOLDER \
		if args.kind == 'replies' else ALL_RT_NETWORKS_FOLDER

	ALL_COMMUNITIES_FOLDER = 'data/twitter_under_stress/communities'

	topic_networks_folder = "/".join([ALL_NETWORKS_FOLDER, args.topic])
	topic_communities_folder = "/".join([ALL_COMMUNITIES_FOLDER, args.topic])

	list_of_graphs = []

	for filename in os.listdir(topic_networks_folder):

		try:

			if args.klcc:
				pattern = "".join([args.granularity, "([0-9]+)",
					"_largest_CC.txt"])
			else:
				pattern = "".join([args.granularity, "([0-9]+)"])

			match = re.search(pattern, filename)

			if match is not None:

				print("At filename:", filename)
				
				num = match.group(1) # the id of the interval

				network_str = "/".join([topic_networks_folder, filename])
				# print("Networks file:\n{}".format(network_str))

				comm_1_str = "".join([topic_communities_folder, "/liberals_",
					args.granularity, str(num), ".txt"])
				comm_2_str = "".join([topic_communities_folder, "/conservatives_",
					args.granularity, str(num), ".txt"])

				# print("Sides files:\n{}\n{}".format(comm_1_str, comm_2_str))

				network = file_utils.load_network_from_file(network_str)
				side_1 = file_utils.load_side_from_file(comm_1_str)
				side_2 = file_utils.load_side_from_file(comm_2_str)

				# # # how many of sides' nodes are in the network?

				all_nodes = set(network.nodes_iter())
				overlap_1 = 100 * len(side_1 & all_nodes) / len(side_1)
				overlap_2 = 100 * len(side_2 & all_nodes) / len(side_2)

				print("nodes of side 1 in network: {:.2f}%".format(overlap_1))
				print("nodes of side 2 in network: {:.2f}%".format(overlap_2))

				cc_a, cc_b = polar_utils.clustering_coefficients(network, side_1, side_2)
				print('Clustering Coefficients: a {:.2f}, b {:.2f}'.format(cc_a, cc_b))

				openness = polar_utils.openness(network, side_1, side_2)
				print('Openness: {:.2f}'.format(openness))

				list_of_graphs.append((num, network))

				# create an output entry

				results['measures'][num] = {'openness': openness, 'cc_a': cc_a, 
					'cc_b': cc_b, 'nodes': len(network),
					'edges': network.size()}

		except Exception as e:

			print(e, file = sys.stderr)

	graph_iter = (g for num, g in list_of_graphs)
	strong_ties_per_node = polar_utils.find_strong_ties(graph_iter, args.alpha)

	for num, g in list_of_graphs:
		tie_strength = polar_utils.tie_strength(g, strong_ties_per_node)
		print(num, tie_strength)
		results['measures'][num]['tie_strength'] = tie_strength

	output_filename = ".".join([args.kind, args.topic, args.granularity,
		"{:.2f}".format(args.alpha), "out"])
	output_path = '/'.join([args.output_folder, output_filename])

	result_str = json.dumps(results)
	with open(output_path, 'w') as output:
		print(result_str, file = output)


