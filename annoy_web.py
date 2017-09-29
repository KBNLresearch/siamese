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

import annoy_indexer

from bottle import request
from bottle import response
from bottle import route
from bottle import run

@route('/query')
def index():
    urn = request.params.get('urn')
    nns = request.params.get('nns')
    step = request.params.get('step')
    vectors = request.params.get('vectors')

    if not urn:
        abort(400, 'No fitting argument ("urn=...") given.')

    if urn.startswith('http://resolver.kb.nl'):
        urn = urn.split('=')[1]

    if nns and step:
        results = indexer.query_all(urn, n_nns=[int(nns)],
                step_sizes=[int(step)], vectors=vectors)
    else:
        results = indexer.query_all(urn, n_nns=[10, 1], step_sizes=[50, 1],
                exclude_self=True, vectors=vectors)

    response.set_header('Content-Type', 'application/json')
    return results

@route('/random')
def random():
    images = indexer.get_random_images()
    response.set_header('Content-Type', 'application/json')
    return {'images': images}

if __name__ == '__main__':
    indexer = annoy_indexer.AnnoyIndexer(vector_dir='vectors',
            index_dir='indices-eucl', n_dimensions=2048, metric='euclidean')
    indexer.load(step_sizes=[50, 1])

    run(host='localhost', port=5050)

