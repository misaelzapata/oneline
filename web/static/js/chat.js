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

    $("#request-client").click(function() {
        updater.socket.send(JSON.stringify({'type':'get_next_client'}));
        $("#request-client").css("display", "none");
    });

    $("#send-message").click(function(e){
        newMessage();
        return false;
    });

    $("#message").on("keypress", function(e) {
        if (e.keyCode == 13) {
            newMessage();
            return false;
        }
    });
    $("#message").select();
    // To do- update client_list, operator list, and set current_client_focus to last message, and add on click event
    updater.start();
    updater.loadClients();
});

function newMessage() {
    var message = {}
    message["type"] = "response_to_contact";
    message["contact"] = updater.current_client;
    message["message"] = $("#message").val();
    message["operator_id"] = "(You)";
    console.log(message);
    updater.socket.send(JSON.stringify(message));
    $("#message").val("").select();
    message["id"] = "";
    updater.showMessage(message);
    updater.magicScroll();
}

var updater = {
    socket: null,

    current_op : $("#current-op"),

    current_client: null,

    client_list: $("#client-list"),

    operator_list: $("#operator-list"),

    chat_window: $("#inbox"),

    start: function() {
        var url = "ws://1line.droptek.com.ar:8080/chat";
        updater.socket = new WebSocket(url);
        updater.socket.onmessage = function(event) {
            var response = JSON.parse(event.data);
            console.log(response);
            strategy = {
                "new_message_alert": function(message){$("#request-client").css("display", "block")},
                "operators_status": function(message){updater.updateOperatorList(message)},
                "new_message": function(message){updater.dealWithClient(message)},
                "new_client": function(message){updater.addOrUpdateClient(message)},
                "send_contact_request": function(message){updater.operatorRequest(message)},
                "response_contact_request": function(message){updater.responseToContactRequest(message)},
            }
            strategy[response.type](response);
        }
    },

    responseToContactRequest: function(message){
        alert("Your request to " +message.to_operator_id + " to deal with " + message.contact + "has been: " + message.status);
    },

    operatorRequest: function(message){
        var status = confirm("Operator: " + message.from_operator_id + " wants you to deal with client : " + message.contact + " and he says: " + message.message);
        if (status == true){
            message.type = "response_contact_request";
            message.status = "accepted";
            consolelog(response);
            updater.socket.send(JSON.stringify(response));
        }else{
            message.type = "response_contact_request";
            message.status = "denied";
            console.log(response);
            updater.socket.send(JSON.stringify(response));
        }
    },

    passClientToOperator: function(operator){
        if (updater.current_client != null){

            var message = prompt("Are you sure you want to send the client " + updater.current_client + " to the operator " + $(operator).attr("id"))
                if (message != null) {
                    var request = {"type":"request_contact_to_operator", "message": message,
                                   "contact": updater.current_client, "to_operator_id":$(operator).attr("name")}
                    console.log(request);
                    updater.socket.send(JSON.stringify(request));
                }
        }
    },

    appendOperator: function(data){
        if(data._id != updater.current_op.attr("value")){
            status = updater.operator_list.prepend($("<hr>", {class:"hr-clas-low"}));
            var operator_dom = $('<div>', {style:"cursor:pointer;", name:data._id});
            var operator_data_dom = $('<img/>',
                                    {src:"static/img/user.png",
                                     alt:"bootstrap Chat box user image",
                                     name: data._id,
                                     class:"img-circle"});
            operator_dom.html(" - " + data.first_name + " " + data.last_name);
            operator_dom.prepend(operator_data_dom);
            operator_dom.click(function(e){updater.passClientToOperator(e.target)});
            updater.operator_list.prepend(operator_dom);
        }
    },

    updateOperatorList: function(message){
        updater.operator_list.empty();
        for (n in message.connected){
            updater.appendOperator(message.connected[n]);
        }
    },

    magicScroll: function(){
        updater.chat_window.animate({scrollTop: updater.chat_window[0].scrollHeight - updater.chat_window[0].clientHeight}, 1000);
    },

    loadClients: function(){
        updater.client_list.empty();
        $.get("get_clients_operator",
            function(data, status){
            for (n in data.clients){
                message = {};
                message.contact = data.clients[n];
                updater.addOrUpdateClient(message);
            }
        })
    },

    loadHistory: function(client){
        updater.chat_window.empty();
        updater.current_client = client.attr("name");
        $.get("history?contact="+ client.attr("name"),
                function(data, status){
                    for (n in data.conversation){
                        updater.showMessage(data.conversation[n]);
                    }
                    updater.magicScroll()
                })
    },

    appendClient: function(message){
        updater.client_list.prepend($("<hr>", {class:"hr-clas-low"}));
        var client_dom = $('<div>', {class:"chat-box-online-left",
                                     style:"cursor:pointer",
                                     id:message.contact.split("@")[0],
                                     name:message.contact});
        var client_data_dom = $('<img />',
                                {src:"static/img/user.png",
                                 alt:"bootstrap Chat box user image",
                                 name:message.contact,
                                 class:"img-circle"});
        client_dom.html(message.contact);
        client_dom.prepend(client_data_dom);
        client_dom.click(function(e){updater.loadHistory($(e.target))});
        updater.client_list.prepend(client_dom);
    },

    addOrUpdateClient: function(message){
        var existing = $("#" + message.contact.split("@")[0]);

        if (existing.length == 0){
            updater.appendClient(message);
            updater.loadHistory($("#" + message.contact.split("@")[0]));
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
            updater.loadHistory($("#" + response.contact.split("@")[0]));
        } else {
            updater.addOrUpdateClient(message)
        }
    },

    showMessage: function(message) {
        var existing = $("#m" + message.id);
        if (existing.length > 0) return;
        var body = $('<div>',
                    {class:"chat-box-right message",
                    id:message.id});
        var username = $('<div>', {class:"chat-box-name-right"});
        var img_username = $('<img />', {class:"img-circle", src:"static/img/user.png"});
        body.prepend(message.message);
        if (!message.operator_id){
            name = message.contact
        }else{
            name = message.operator_id
        }
        username.html("- " + name);
        username.prepend(img_username);
        updater.chat_window.append(body);
        updater.chat_window.append(username);
        updater.chat_window.append($("<hr>", {class:"hr-clas-low"}));
    }
};
