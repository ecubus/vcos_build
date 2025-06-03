
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
# is_subdirectory
#
# Description:
#  Check if a directory is a subdirectory of another directory
#
# Usage:
#  is_subdirectory(potential_child potential_parent result_var)
#
# Parameters:
#  potential_child: the directory to be checked
#  potential_parent: the directory to be checked against
#  result_var: the variable to store the result
#
# Example:
#  is_subdirectory("${CMAKE_CURRENT_SOURCE_DIR}/subdir" "${CMAKE_CURRENT_SOURCE_DIR}" result)
#  if(result)
#    message(STATUS "subdir is a subdirectory of ${CMAKE_CURRENT_SOURCE_DIR}")
#  else()
#    message(STATUS "subdir is not a subdirectory of ${CMAKE_CURRENT_SOURCE_DIR}")
#  endif()
# ~~~

function(is_subdirectory potential_child potential_parent result_var)
    get_filename_component(child_abs "${potential_child}" ABSOLUTE)
    get_filename_component(parent_abs "${potential_parent}" ABSOLUTE)
    
    file(RELATIVE_PATH relative_path "${parent_abs}" "${child_abs}")
    if(relative_path MATCHES "^\\.\\./")
        set(${result_var} FALSE PARENT_SCOPE)
    else()
        set(${result_var} TRUE PARENT_SCOPE)
    endif()
endfunction()
