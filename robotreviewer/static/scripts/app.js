/* -*- tab-width: 2; indent-tabs-mode: nil; c-basic-offset: 2; js-indent-level: 2; -*- */
define(function (require) {
  'use strict';

  var Backbone = require("backbone");
  var React = require("react");
  var ReactDOM = require("react-dom");
  var _ = require("underscore");
  var $ = require("jquery");
  var FileUtil = require("spa/helpers/fileUtil");


  // Set CSRF
  var _sync = Backbone.sync;
  Backbone.sync = function(method, model, options){
    options.beforeSend = function(xhr){
      xhr.setRequestHeader('X-CSRF-Token', window.CSRF_TOKEN);
    };
    return _sync(method, model, options);
  };

  // Breadcrumbs hack
  var breadcrumbsModel = new (require("models/breadcrumbs"))();
  var BreadcrumbsComponent = React.createFactory(require("jsx!components/breadcrumbs"));

  var breadcrumbs =
      ReactDOM.render(new BreadcrumbsComponent({breadcrumbs: breadcrumbsModel}),
                                    document.getElementById("breadcrumbs"));

  breadcrumbsModel.on("all", function(e, obj) {
    breadcrumbs.forceUpdate();
  });

  // Component views
  var DocumentView = React.createFactory(require("jsx!views/document"));
  var UploadView = React.createFactory(require("jsx!views/upload"));
  var ReportView = React.createFactory(require("jsx!views/report"));

  var isEditable = true;

  var Router = Backbone.Router.extend({
    routes : {
      "upload" : "upload",
      "report/:reportId" : "report",
      "document/:reportId/:documentId?annotation_type=:type&uuid=:uuid" : "document",
      "document/:reportId/:documentId?annotation_type=:type" : "document",
      "*path" : "upload"
    },
    upload : function() {
      var node = document.getElementById("main");
      ReactDOM.unmountComponentAtNode(node);
      ReactDOM.render(new UploadView({}), node);
      breadcrumbsModel.reset(
        [{link: "/#upload", title: "upload"}]);
    },
    report : function(reportId) {
      var node = document.getElementById("main");
      ReactDOM.unmountComponentAtNode(node);
      ReactDOM.render(new ReportView({reportId: reportId}), node);
      breadcrumbsModel.reset(
        [{link: "/#upload", title: "upload"},
         {link: "/#report/" + reportId, title: "report"}
        ]);
    },
    document : function(reportId, documentId, type, uuid) {
      var node = document.getElementById("main");
      ReactDOM.unmountComponentAtNode(node);

      // Models
      var documentModel = new (require("spa/models/document"))();
      var marginaliaModel = new (require("spa/models/marginalia"))();
      var next_link = '#';
      var spare_time = 0;
      var url = window.location.href;
      var url_parts = url.split("?");
      var query_str = url_parts[1].split("&");
      var ux_uuid = 'id';
      var flag = 1;
      var task_id = 1;
      for(var key in query_str){
        var kv = query_str[key].split("=");
        if(kv[0] == 'ux_uuid'){
          ux_uuid = kv[1];
        }
        if(kv[0] == 'flag'){
          flag = kv[1];
        }
        if(kv[0] == 'task_id'){
          task_id = kv[1];
        }
      }

      var marginaliaUrl = "/marginalia/" + reportId + "/" + documentId + "?annotation_type=" + type + "&ux_uuid=" + ux_uuid + "&task_id=" + task_id;
      $.get(marginaliaUrl, function(data) {
        var marginalia = {marginalia: JSON.parse(data)};
        marginaliaModel.reset(marginaliaModel.parse(marginalia));
        if(uuid) {
          marginaliaModel.setActiveByUuid(uuid);
        }
      });

      var documentUrl = "/pdf/" + reportId + "/" + documentId;
      documentModel.loadFromUrl(documentUrl, uuid);

      var nextUrl = "/get_next/" + documentId + '?ux_uuid=' + ux_uuid + '&flag=' + flag;
      $.ajax({
        url: nextUrl,
        type: "POST",
        async: false,
        success: function(data) {
          next_link = JSON.parse(data);
          //next_link = '/#document/' + urls[0] + '/' + urls[1] + '?annotation_type=' + type + "&ux_uuid=" + ux_uuid;
        },
        error: function(err){
          //alert(err.toSource());
        }
      });

      var timeUrl = '/get_time/' + reportId + '/' + documentId + '/' + ux_uuid;
      $.ajax({
        url: timeUrl,
        type: "POST",
        async: false,
        success: function(data) {
          spare_time = parseInt(JSON.parse(data)); // in sec
        }
      });

      ReactDOM.render(
        new DocumentView({document: documentModel,
                          marginalia: marginaliaModel,
                          next_link: next_link,
                          time_spent: spare_time,
                          isEditable: isEditable}),
        node);

      breadcrumbsModel.reset(
        [{link: "/#upload", title: "upload"},
         {link: "/#report/" + reportId, title: "report"},
         {link: "/#document/" + reportId + "/" + documentId, title: "document"}
        ]);
    }
  });

  window.router = new Router();


  Backbone.history.start();

});
