#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Juliette Lonij, Koninklijke Bibliotheek -
# National Library of the Netherlands
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import glob
import os
import numpy as np
import pickle
import random
import requests

from annoy import AnnoyIndex

class AnnoyIndexer:

    def __init__(self, vector_dir, index_dir, n_dimensions, metric='angular'):
        '''
        Initialize class variables.
        '''
        self.vector_dir = vector_dir
        self.index_dir = index_dir
        self.n_dimensions = n_dimensions
        self.metric = metric

    def build(self, n_trees, step_sizes):
        '''
        Build indices for given step sizes.
        '''
        path = os.path.join(self.vector_dir, '*')
        years = [int(os.path.split(y)[-1]) for y in glob.glob(path)]

        path = os.path.join(self.vector_dir, '*', '*.npy')
        vector_files = sorted(glob.glob(path))

        for step in step_sizes:
            for start_year in range(min(years), max(years) + 1, step):
                print('Indexing {} year(s) from {} ...'.format(step, start_year))

                step_years = range(start_year, start_year + step)

                to_index = [v for v in vector_files if int(v.split(os.sep)[-2])
                        in step_years]

                t = AnnoyIndex(self.n_dimensions, self.metric)
                for i, vector_file in enumerate(to_index):
                    #print('Processing {} ...'.format(vector_file))
                    t.add_item(i, np.load(vector_file))

                print('Building {} trees ...'.format(n_trees))
                t.build(n_trees)

                print('Saving index and identifiers ...')
                save_path = os.path.join(self.index_dir, str(step))
                os.makedirs(save_path, exist_ok=True)
                index_file = os.path.join(self.index_dir, str(step),
                        '{}.ann'.format(start_year))
                t.save(index_file)

                urns = [self.vector_to_urn(v) for v in to_index]
                urn_file = index_file.replace('.ann', '.pkl')
                pickle.dump(urns, open(urn_file, 'wb'))

    def load(self, step_sizes=[]):
        '''
        Load index files and create vector file dict.
        '''
        print('Building available vector files dict ...')
        path = os.path.join(self.vector_dir, '*', '*.npy')

        urn_to_year = {}
        for p in sorted(glob.glob(path)):
            urn = self.vector_to_urn(p.split(os.sep)[-1])
            year = int(p.split(os.sep)[-2])
            urn_to_year[urn] = year
        self.urn_to_year = urn_to_year

        print('Loading Annoy indices ...')
        path = os.path.join(self.index_dir, '*', '*.ann')

        indices = []
        for p in sorted(glob.glob(path)):
            index = {}
            index['step'] = int(p.split(os.sep)[-2])
            if not step_sizes or index['step'] in step_sizes:

                print('Loading index file {} ...'.format(p))
                t = AnnoyIndex(self.n_dimensions, self.metric)
                t.load(p)

                index['index'] = t
                index['start'] = int(os.path.splitext(p.split(os.sep)[-1])[0])
                index['urns'] = pickle.load(open(p.replace('.ann', '.pkl'), 'rb'))
                indices.append(index)

        self.indices = indices

    def query_indices(self, vector, n_nns, step):
        '''
        Query indices of given step size by vector.
        '''
        to_query = [i for i in self.indices if i['step'] == step]

        results = {}
        for index in to_query:
            nn = index['index'].get_nns_by_vector(vector, n=n_nns,
                    search_k=10000, include_distances=True)

            result = []
            for i, n in enumerate(nn[0]):
                neighbor = {}
                neighbor['urn'] = index['urns'][n]
                neighbor['year'] = self.urn_to_year[index['urns'][n]]
                neighbor['path'] = os.path.join(str(neighbor['year']),
                        self.urn_to_image(neighbor['urn']))
                neighbor['distance'] = nn[1][i]
                result.append(neighbor)

            results[index['start']] = result

        return results

    def query_all(self, urn, step_sizes, n_nns, exclude_self=False,
            vectors=False):
        '''
        Query indices for multiple step sizes by urn.
        '''
        result = {}

        data = self.get_metadata(urn)
        source = {}
        source['urn'] = urn
        source['year'] = data['year']
        source['image'] = data['image']
        if vectors:
            source['vector'] = data['vector'].tolist()
        result['source'] = source

        result['neighbors'] = {}
        for i, step in enumerate(step_sizes):
            if exclude_self:
                neighbors = self.query_indices(data['vector'],
                        n_nns=n_nns[i] + 1, step=step)
                for start, neighbor_list in neighbors.items():
                    neighbors[start] = [n for n in neighbors[start] if
                            n['urn'] != urn][:n_nns[i]]
            else:
                neighbors = self.query_indices(data['vector'],
                    n_nns=n_nns[i], step=step)
            if vectors:
                for start, neighbor_list in neighbors.items():
                    for n in neighbor_list:
                        n['vector'] = self.load_vector(n['urn']).tolist()

            result['neighbors'][step] = neighbors

        return result

    def get_metadata(self, urn):
        '''
        Retrieve metadata from file, if avaiable.
        '''
        data = {}
        if urn in self.urn_to_year:
            data['year'] = self.urn_to_year[urn]
            data['image'] = self.urn_to_image(urn)
            data['vector'] = self.load_vector(urn)
        else:
            data = None
        return data

    def get_random_images(self):
        '''
        Return a number of random images from the set.
        '''
        images = []
        urns = list(self.urn_to_year)
        for i in range(10):
            urn = random.choice(urns)
            image = {}
            image['urn'] = urn
            image['year'] = self.urn_to_year[urn]
            image['path'] = os.path.join(str(image['year']),
                    self.urn_to_image(urn))
            images.append(image)
        return images

    def vector_to_urn(self, vector):
        '''
        Convert vector filename to urn.
        '''
        urn = vector.split(os.sep)[-1]
        urn = os.path.splitext(urn)[0].replace('-', ':')
        return urn

    def urn_to_vector(self, urn):
        '''
        Convert urn to vector filename.
        '''
        vector = urn.replace(':', '-') + '.npy'
        return vector

    def urn_to_image(self, urn):
        '''
        Convert urn to image filename.
        '''
        vector = urn.replace(':', '-') + '.jpg'
        return vector

    def load_vector(self, urn):
        '''
        Load numpy array from file.
        '''
        path = os.path.join(self.vector_dir, str(self.urn_to_year[urn]))
        path = os.path.join(path, self.urn_to_vector(urn))
        return np.load(path)


if __name__ == '__main__':
    indexer = AnnoyIndexer(vector_dir='vectors', index_dir='indices-manh',
            n_dimensions=2048, metric='manhattan')
    indexer.build(n_trees=100, step_sizes=[1, 50])
