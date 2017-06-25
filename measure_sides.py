"""
a script to measure polarized networks
"""
import sys, os
import polarlib.file_utils as file_utils
import polarlib.polar_utils as polar_utils
import polarlib.math_utils as math_utils
import polarlib.network_utils as network_utils
import argparse
import json
import re
import networkx as nx


if __name__ == '__main__' :

	# parse arguments

	parser = argparse.ArgumentParser()
	parser.add_argument('kind', choices = ['retweets', 'replies'],
		default = 'retweets',
		help = 'What kind of networks to analyze.')
	parser.add_argument('topic', help = 'keyword defining the topic')
	parser.add_argument('granularity', choices = ['week', 'month', 'day'],
		help = 'Granularity.')
	parser.add_argument('--core', action = 'store_true',
		help = 'Perform analysis only core')
	parser.add_argument('-a', '--alpha', type = float, default = 0.10,
		help = 'Top ties fraction.')
	parser.add_argument('-o', '--output_folder',
		default = 'stressed_polarization/results',
		help = 'Folder where to store results.')

	args = parser.parse_args()

	# this is where we store all the results
	results = {'settings': {'granularity': args.granularity, 'topic': args.topic,
			'alpha': args.alpha}, 'measures': {}}

	## using global fixed sides

	side_1_file = "".join(['data/twitter_under_stress/communities/',
		args.topic,'/liberals_full.txt'])
	side_1 = file_utils.load_side_from_file(side_1_file)

	side_2_file = "".join(['data/twitter_under_stress/communities/',
		args.topic,'/conservatives_full.txt'])
	side_2 = file_utils.load_side_from_file(side_2_file)

	
	# go over networks
	ALL_RT_NETWORKS_FOLDER = 'data/twitter_under_stress/networks'
	ALL_MT_NETWORKS_FOLDER = 'data/twitter_under_stress/reply_networks'
	ALL_NETWORKS_FOLDER = ALL_MT_NETWORKS_FOLDER if args.kind == 'replies' \
		else ALL_RT_NETWORKS_FOLDER

	# these networks are constructed from both the 1% sample and the 
	# twitter crawl
	topic_networks_folder = "/".join([ALL_NETWORKS_FOLDER, args.topic])

	list_of_graphs = []

	for filename in os.listdir(topic_networks_folder):

		try:

			pattern = "".join([args.granularity, "([0-9]+)$"])
			match = re.search(pattern, filename)

			if match is not None:

				print("At filename:", filename)
				
				num = match.group(1) # the id of the interval

				network_str = "/".join([topic_networks_folder, filename])

				full_network = file_utils.load_network_from_file(network_str,
					is_directed = True)

				# choose the actual network we'll be working with

				if args.core:
					# if we are working with the core, then separate
					# core and periphery

					## TODO load from files
					core_filename = "data/cores/" + args.topic + ".core"
					core_nodes = file_utils.load_core_from_file(core_filename)
					periphery_nodes = set(full_network.nodes_iter()) - core_nodes

					# print("We got {} core nodes and {} periphery nodes"\
					# 	.format(len(core_nodes), len(periphery_nodes)))

					network = full_network.subgraph(core_nodes)
					# network.add_nodes_from(core_nodes) # all core nodes

					full_undir_graph = nx.Graph(full_network)
					core_periphery_openness = \
						polar_utils.normalized_openness(full_undir_graph,
							core_nodes, periphery_nodes)

					core_density = network_utils.core_concentration(network, full_network)

					core_triplets = network_utils.core_edge_triplets(network, full_network)

				else:

					network = full_network

				undir_graph = nx.Graph(network)
				# cc_a, cc_b = polar_utils.clustering_coefficients(undir_graph, side_1, side_2)
				cc_a, cc_b = polar_utils.normalized_ccs(undir_graph, side_1, side_2)

				openness = polar_utils.normalized_openness(undir_graph, side_1, side_2)

				# bimotif_ratio = polar_utils.bimotif_fraction(network)
				bimotif_ratio = polar_utils.normalized_bimotif(network)

				side_tuple = polar_utils.side_edge_tuples(network, side_1, side_2)

				list_of_graphs.append((num, network))

				# create an output entry

				results['measures'][num] = {'openness': openness, 'cc_a': cc_a, 
					'cc_b': cc_b, 'nodes': len(network),
					# 'in_degree_scale': in_degree_scale,
					# 'out_degree_scale': out_degree_scale,
					'edges': network.size(),
					'bimotif_ratio': bimotif_ratio,
					'side_tuple': side_tuple}

				if args.core:
					results['measures'][num]['core_periphery_openness'] = core_periphery_openness
					results['measures'][num]['density'] = core_density
					results['measures'][num]['core_triplets'] = core_triplets
					# results['measures'][num]['uni_density'] = core_uni_density

		except Exception as e:

			# print(e, file = sys.stderr)
			raise e

	graph_iter = (nx.Graph(g) for num, g in list_of_graphs)
	strong_ties_per_node = polar_utils.find_strong_ties(graph_iter, args.alpha)

	for num, g in list_of_graphs:
		tie_strength = polar_utils.normalized_tie_strength(g, strong_ties_per_node)
		results['measures'][num]['tie_strength'] = tie_strength

	output_filename = ".".join((["core"] if args.core else []) + [args.kind,
		args.topic, args.granularity, "{:.2f}".format(args.alpha), "out"])
	output_path = '/'.join([args.output_folder, output_filename])

	result_str = json.dumps(results)
	with open(output_path, 'w') as output:
		print(result_str, file = output)


