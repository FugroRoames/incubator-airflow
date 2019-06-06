# -*- coding: utf-8 -*-
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from typing import Any, List
from airflow.models import DagBag


def list_dags(argument: Any, value: Any) -> List[Any]:
    """Return a list of Dags matching the given DAG default argument value."""
    dagbag = DagBag()

    def should_keep_dag(dag: Any) -> bool:
        return any(
            [
                not argument or not value,
                argument in dag.default_args and dag.default_args[argument] == value,
            ],
        )

    return [
        dag_id
        for (dag_id, dag) in dagbag.dags.items()
        if should_keep_dag(dag)
    ]
