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
    console.log(message);
    console.log(JSON.stringify(message));
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

    client_list: $("#client-list"),

    operator_list: $("#operator-list"),

    start: function() {
        var url = "ws://127.0.0.1:8080/chat";
        updater.socket = new WebSocket(url);
        updater.socket.onmessage = function(event) {
            var response = JSON.parse(event.data);
            console.log(response);
            strategy = {
                "new_message_alert": function(message){$("#request-client").css("display", "block")},
                "operators_status": function(message){updater.updateOperatorList(message)},
                "new_client": function(message){updater.appendClient(message)},
                "new_message": function(message){ updater.addOrUpdateClient(message); updater.showMessage(message)}
            }
            strategy[response.type](response);
        }
    },

    appendOperator: function(data){

        updater.operator_list.prepend($("<hr>", {class:"hr-clas-low"}));
        var operator_dom = $('<div>', {style:"cursor:pointer;", id:data._id});
        var operator_data_dom = $('<img/>',
                                {src:"static/img/user.png",
                                 alt:"bootstrap Chat box user image",
                                 class:"img-circle"});
        operator_dom.html(" - " + data.first_name + " " + data.last_name);
        operator_dom.prepend(operator_data_dom);
        operator_dom.click(function(e){alert("coming soon!")});
        updater.operator_list.prepend(operator_dom);
    },

    updateOperatorList: function(message){
        updater.operator_list.empty();
        for (n in message.connected){
            console.log(n)
            updater.appendOperator(message.connected[n]);
        }
    },

    appendClient: function(message){
        updater.client_list.prepend($("<hr>", {class:"hr-clas-low"}));
        var client_dom = $('<div>', {class:"chat-box-online-left", style:{cursor:"pointer"}, id:message.contact});
        var client_data_dom = $('<img />',
                                {src:"static/img/user.png",
                                 alt:"bootstrap Chat box user image",
                                 class:"img-circle"});
        client_dom.html(message.contact);
        client_dom.prepend(client_data_dom);
        client_dom.click(function(e){updater.current_client = e.target.id;});
        updater.client_list.prepend(client_dom);
    },

    addOrUpdateClient: function(message){
        var existing = $(message.contact);
        if (existing.length == 0){
            updater.appendClient(message);
        }else{
            existing.css("background-color","grey")
        }

    },

    dealWithClient: function(response){
        if (updater.current_client == null){
            updater.current_client = response.contact;
            updater.appendClient(response);
        };
        if (updater.current_client == response.contact){
            updater.showMessage(response);
        } else {
            updater.addOrUpdateClient(message)
        }
    },

    showMessage: function(message) {
        var existing = $("#m" + message.id);
        console.log(existing.length);
        if (existing.length > 0) return;
        var node = $(message.html);
        node.hide();
        $("#inbox").append(node);
        node.slideDown();
    }
};
