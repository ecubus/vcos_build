# This Python file uses the following encoding: utf-8
############################################################################
# Copyright (c) 2025 Li Auto Inc. and its affiliates
# Licensed under the Apache License, Version 2.0(the "License");
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
############################################################################
import json

OS_ECUC_PATH = "config/bsw/Os/Os_ecuc.arxml"
SCH_TABLE_PATH = "config/system/schedule_table.json"
def process_schedule_tables(data):
    # 处理每个调度表
    for table_name, schedule in data.items():
        if not schedule:
            continue

        # 第一个元素是基准，我们将其他任务名合并到这里
        first_entry = schedule[0]
        if len(schedule) < 2:
            continue

        # 收集所有任务名（跳过第一个，因为它已经在基准中）
        for entry in schedule[1:]:
            if len(entry) >= 2:
                first_entry += entry[1:]

        # 只保留第一个元素
        data[table_name] = [first_entry]

    return data

def save_schedule_json(file_path):
    # 1. 读取JSON文件
    input_file = file_path  # 替换为你的JSON文件路径
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 2. 处理数据
    processed_data = process_schedule_tables(data)

    # 3. 保存回原文件
    with open(input_file, 'w', encoding='utf-8') as f:
        json.dump(processed_data, f, indent=2, ensure_ascii=False)