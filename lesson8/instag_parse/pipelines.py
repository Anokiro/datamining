# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
# from itemadapter import ItemAdapter
import pickle
import sys

class InstaParsePipeline:

    def process_item(self, item, spider):
        with open(spider.file, 'rb') as file:
            graph_file = pickle.load(file)
        graph_file['data'][item['side']][item['id']] = item['graph']
        graph_file['data'][item['side']]['all'].update(item['graph'])
        another_side = str(2 // int(item['side']))
        if item['id'] in graph_file['data'][another_side]['all']:
            graph_file['have_any_way'] = True
            graph_file['data']['1'].update(graph_file['data']['2'])
            all_graph = graph_file['data']['1']
            start_follow = graph_file['target_user'][0]
            end_follow = graph_file['target_user'][1]

            graph_file['way_list'] = self.searchpath(all_graph, start_follow, end_follow)
            with open(spider.file, 'wb') as file_n:
                pickle.dump(graph_file, file_n)
            sys.exit()
        with open(spider.file, 'wb') as file_n:
            pickle.dump(graph_file, file_n)
        return item

    def searchpath(self, graph, start_follow, end_follow):
        first = [None] * (len(graph) + 1)
        second = [None] * (len(graph) + 1)
        first[start_follow] = 0
        in_start = [start_follow]
        qstart = 0
        while qstart < len(in_start):
            use = in_start[qstart]
            qstart += 1
            for iter_item in graph[use]:
                if first[iter_item] is None:
                    second[iter_item] = use
                    first[iter_item] = first[use] + 1
                    in_start.append(iter_item)
        answer = []
        curr = end_follow
        while curr is not None:
            answer.append(curr)
            curr = second[curr]
        return answer