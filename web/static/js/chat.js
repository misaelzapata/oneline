// Copyright 2009 FriendFeed
//
// Licensed under the Apache License, Version 2.0 (the "License"); you may
// not use this file except in compliance with the License. You may obtain
// a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
// WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
// License for the specific language governing permissions and limitations
// under the License.

$(document).ready(function() {
    if (!window.console) window.console = {};
    if (!window.console.log) window.console.log = function() {};

    $("#messageform").on("submit", function() {
        newMessage($(this));
        return false;
    });
    $("#messageform").on("keypress", function(e) {
        if (e.keyCode == 13) {
            newMessage($(this));
            return false;
        }
    });
    $("#message").select();
    // To do- update client_list, operator list, and set current_client_focus to last message, and add on click event
    updater.start();
});

function newMessage(form) {
    var message = form.formToDict();
    updater.socket.send(JSON.stringify(message));
    form.find("input[type=text]").val("").select();
}

jQuery.fn.formToDict = function() {
    var json = {}
    json["type"] = "response_to_contact";
    json["contact"] = updater.current_client;
    json["message"] = this.find("#message").value();
    return json;
};

var updater = {
    socket: null,

    current_client: null,

    start: function() {
        var url = "ws://127.0.0.1:8080/chat";
        updater.socket = new WebSocket(url);
        updater.socket.onmessage = function(event) {
            if (updater.current_client == null){
                updater.current_client = event.data.contact;
            };
            if (updater.current_client == event.data.contact){
                updater.showMessage(JSON.parse(event.data));
            } else {
                // do something with the client list, if not present, append at the top.
            }
        }
    },

    showMessage: function(message) {
        var existing = $("#m" + message.id);
        if (existing.length > 0) return;
        var node = $(message.html);
        node.hide();
        $("#inbox").append(node);
        node.slideDown();
    }
};
