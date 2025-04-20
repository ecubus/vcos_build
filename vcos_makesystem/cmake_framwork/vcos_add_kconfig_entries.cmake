
# ##############################################################################
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
# ##############################################################################

# ~~~
# vcos_add_kconfig_entries
#
# Description:
#  Overwrite or modify kconfig entries in defconfig file according to user's input.
#
# Usage:
#  vcos_add_kconfig_entries( [OVERWRITE] DEFCONFIG_FILE <string> CONFIGS <list> )
#
# Parameters:
#  OVERWRITE: overwrite defconfig
#  DEFCONFIG_FILE: defconfig file path
#  CONFIGS: list of kconfig entries to be added or modified
#
# Example:
#  overwrite defconfig:
#    vcos_add_kconfig_entries(OVERWRITE DEFCONFIG_FILE ${DEFCONFIG_FILE} CONFIGS ${CONFIGS})
#
#  append defconfig:
#    vcos_add_kconfig_entries(DEFCONFIG_FILE ${DEFCONFIG_FILE} CONFIGS ${CONFIGS})
#
# ~~~

function(vcos_add_kconfig_entries)
    # parse arguments
    cmake_parse_arguments(
        ARG                # arguments prefix
        "OVERWRITE"        # optional argument: overwrite defconfig; default append.
        "DEFCONFIG_FILE"   # single argument: defconfig file path
        "CONFIGS"          # list argument：CONFIG_NAME=value
        ${ARGN}            #
    )

    # check necessary defconfig file
    if(NOT ARG_DEFCONFIG_FILE)
        message(FATAL_ERROR "MUST specify DEFCONFIG_FILE !")
    endif()

    # check necessary configs
    if(NOT ARG_CONFIGS)
        message(FATAL_ERROR "MUST input at lease one CONFIGS !")
    endif()

    # process configs
    set(config_dict)
    foreach(config ${ARG_CONFIGS})
        # parse config name and value (CONFIG_NAME=value)
        string(REGEX MATCH "([^=]*)=(.*)" _ ${config})
        if(NOT CMAKE_MATCH_1)
            message(FATAL_ERROR "Invalid config argument ${config}, should be 'CONFIG_NAME=value' !")
        endif()
        list(APPEND config_dict ${CMAKE_MATCH_1} ${CMAKE_MATCH_2})
    endforeach()

    if(ARG_OVERWRITE)
        # overwrite defconfig
        file(WRITE ${ARG_DEFCONFIG_FILE} "")
    else()
        # ensure defconfig file exists
        if(NOT EXISTS ${ARG_DEFCONFIG_FILE})
            file(WRITE ${ARG_DEFCONFIG_FILE} "")
        endif()
        file(READ ${ARG_DEFCONFIG_FILE} content)
    endif()

    string(REGEX REPLACE "\r\n" "\n" content "${content}")
    string(REGEX REPLACE "\r" "\n" content "${content}")
    string(REGEX REPLACE "\n+" "\n" content "${content}")
    string(REGEX REPLACE "\n" ";" lines "${content}")

    set(new_lines)
    foreach(line ${lines})
        string(REGEX MATCH "^([A-Za-z0-9_]+)=.*" match ${line})
        if(match)
            set(key ${CMAKE_MATCH_1})
            # check if key exists in config_dict
            list(FIND config_dict ${key} index)
            if(NOT index LESS 0)
                # exists, replace value
                math(EXPR value_index "${index} + 1")
                list(GET config_dict ${value_index} value)
                set(new_line "${key}=${value}")
                list(APPEND new_lines ${new_line})
                # remove key and value from config_dict
                list(REMOVE_AT config_dict ${index} ${value_index})
            else()
                list(APPEND new_lines ${line})
            endif()
        else()
            # not config line, append
            list(APPEND new_lines ${line})
        endif()
    endforeach()

    # add new configs
    list(LENGTH config_dict config_dict_LENGTH)
    math(EXPR CONFIG_LENGTH "${config_dict_LENGTH} - 1")
    if(NOT config_dict_LENGTH EQUAL 0)
        foreach(i RANGE 0 ${CONFIG_LENGTH} 2)
            list(GET config_dict ${i} key)
            math(EXPR value_index "${i} + 1")
            list(GET config_dict ${value_index} value)
            list(APPEND new_lines "${key}=${value}")
        endforeach()
    endif()

    # write content to defconfig file
    string(REPLACE ";" "\n" new_content "${new_lines}")
    file(WRITE ${ARG_DEFCONFIG_FILE} "${new_content}")

    message(STATUS "configs already update into ${ARG_DEFCONFIG_FILE}")
endfunction()