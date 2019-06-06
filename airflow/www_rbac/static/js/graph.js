/**
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements. See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership. The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License. You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied. See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */

import { generateTooltipDateTime, converAndFormatUTC } from './datetime-utils';
import { escapeHtml } from './base';

// Assigning css classes based on state to nodes
// Initiating the tooltips
function update_nodes_states(task_instances) {
  $.each(task_instances, function (task_id, ti) {
    $('tspan').filter(function (index) {
      return $(this).text() === task_id;
    })
      .parent().parent().parent().parent().parent().parent().parent()
      .attr("class", "node enter " + (ti.state ? ti.state : "no_status"))
      .attr("data-toggle", "tooltip")
      .attr("data-original-title", function (d) {
        // Tooltip
        const task = tasks[task_id];
        let tt = "";
        if(ti.task_id != undefined) {
          tt +=  "Task_id: " + escapeHtml(task.task_id) + "<br>";
        }
        tt += "Run: " + converAndFormatUTC(task.execution_date) + "<br>";
        if(ti.run_id != undefined) {
          tt += "run_id: <nobr>" + escapeHtml(task.run_id) + "</nobr><br>";
        }
        tt += "Operator: " + escapeHtml(task.task_type) + "<br>";
        tt += "Duration: " + escapeHtml(task.duration) + "<br>";
        tt += "Started: " + escapeHtml(ti.start_date) + "<br>";
        tt += generateTooltipDateTime(ti.start_date, ti.end_date, dagTZ); // dagTZ has been defined in dag.html
        return tt;
      });
      var exist = $('#progress_' + task_id).length;
      if (exist > 0) {
          $('#progress_completed_' + task_id).width(ti.progress.completed.toString() + '%');
          $('#progress_warning_' + task_id).width(ti.progress.warning.toString() + '%');
          $('#progress_failed_' + task_id).width(ti.progress.failed.toString() + '%');
          $('#progress_ready_' + task_id).width(ti.progress.ready.toString() + '%');
      }
  });
}

function error(msg){
  $('#error_msg').html(msg);
  $('#error').show();
  $('#error').delay(10000).fadeOut('slow');
  $('#loading').hide();
  $('#chart_section').hide(1000);
  $('#datatable_section').hide(1000);
}

function refreshGraph() {
  $("#loading").css("display", "block");
  $("div#svg_container").css("opacity", "0.2");
  $.get(getTaskInstanceURL)
    .done(
      function (task_instances) {
        update_nodes_states(JSON.parse(task_instances));
        $("#loading").hide();
        $("div#svg_container").css("opacity", "1");
        $('#error').hide();
      }
    ).fail(function (jqxhr, textStatus, err) {
    $('#error_msg').html(textStatus + ': ' + err);
    $('#error').show();
    $('#loading').hide();
    $('#chart_section').hide(1000);
    $('#datatable_section').hide(1000);
  });
}

function autoRefreshGraph() {
  $.get(getTaskInstanceURL, getTaskInstanceParams)
    .done(
      function(task_instances) {
          update_nodes_states(JSON.parse(task_instances));
      }
    );
}

function initRefreshButton() {
  d3.select("#refresh_button").on("click", refreshGraph);
}

initRefreshButton();
update_nodes_states(task_instances);

var refresh_interval = null;
if (refresh_rate > 0) {
  refresh_interval = window.setInterval(autoRefreshGraph, refresh_rate);
}

d3.select("#stop_auto_refresh_button").on("click", function () {
  clearInterval(refresh_interval);
  $("#stop_auto_refresh_button").hide();
  $("#start_auto_refresh_button").show();
});

d3.select("#start_auto_refresh_button").on("click", function () {
  refresh_interval = window.setInterval(autoRefreshGraph, refresh_rate);
  $("#start_auto_refresh_button").hide();
  $("#stop_auto_refresh_button").show();
});

