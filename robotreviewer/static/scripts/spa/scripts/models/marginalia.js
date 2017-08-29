/* -*- tab-width: 2; indent-tabs-mode: nil; c-basic-offset: 2; js-indent-level: 2; -*- */
define(function (require) {
  'use strict';

  var _ = require("underscore");
  var $ = require("jquery");
  var Backbone = require("backbone");
  var Annotation = require('./annotation');

  var startTime = new Date(); // TODO use something like Mixpanel for this

  var colors=[
    [168,191,18],
    [0,170,181],
    [255,159,0],
    [244,28,84],
    [0,67,88],
    [191,4,38],
  ];

  var toClassName = function(str) {
    return str.replace(/ /g, "-").toLowerCase();
  };

  var guid = function() {
    // RFC4122 version 4 compliant
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      var r = Math.random() * 16|0, v = c == 'x' ? r : (r&0x3|0x8);
      return v.toString(16);
    });
  };

  var Annotations = Backbone.Collection.extend({
    model: Annotation
  });

  var Marginalis = Backbone.Model.extend({
    defaults: {
      id: null,
      description: "",
      color: null,
      title: null,
      type: "",
      active: false
    },
    initialize: function(data) {
      var self = this;
      var annotations = new Annotations(data.annotations);
      this.set("annotations", annotations);
      annotations.on("all", function(e, obj)  {
        self.trigger("annotations:" + e, obj);
      });
    },
    toJSON: function() {
      var json = _.clone(this.attributes);
      for(var attr in json) {
        if((json[attr] instanceof Backbone.Model) || (json[attr] instanceof Backbone.Collection)) {
          json[attr] = json[attr].toJSON();
        }
      }
      return json;
    }
  });

  var Marginalia = Backbone.Collection.extend({
    model: Marginalis,
    parse: function(data, options) {
      var marginalia = _.clone(data.marginalia);
      _.each(marginalia, function(marginalis, idx) {
        var id = marginalis.id || toClassName(marginalis.title);
        marginalis.active = idx === false;
        marginalis.id = id;
        marginalis.color = colors[idx % colors.length];
      });
      return marginalia;
    },
    save: _.throttle(function(beforeSend, successCallback, errorCallback) {
      var self = this;
      beforeSend();
      $.ajax({
        url: window.location.href,
        type: "PUT",
        data: {data: JSON.stringify({marginalia: self.toJSON()})},
        headers: {"X-CSRF-Token": CSRF_TOKEN},
        success: function(data) {
          successCallback(data);
        },
        error: function(err) {
          errorCallback(err);
        }
      });
    }, 2500),
    toggleActive: function(marginalia) {
      var isActive = !!marginalia.get("active");
      marginalia.set("active", !isActive);
    },
    getActive: function() {
      return this.where({active: true});
    },
    setActiveByUuid: function(uuid) {
      var active =  this.find(function(m) {
        var annotations = m.get("annotations");
        var uuids = annotations.map(function(a) { return a.get("uuid") });
        return _.contains(uuids, uuid);
      });
      this.forEach(function(m) {
        m.set({active: false});
      });
      this.toggleActive(active);
      return active;

    },
    addAnnotation: function(content) {
      var self = this;
      var marginalia = this.getActive();
      var url = window.location.href.split('?');
      var url_parts = url[0].split("/");
      var pdf_uuid = url_parts[url_parts.length-1];
      var report_uuid = url_parts[url_parts.length-2];
      var query_str = url[1].split("&");
      var ux_uuid = 'id';
      for(var key in query_str){
        var kv = query_str[key].split("=");
        if(kv[0] == 'ux_uuid'){
          ux_uuid = kv[1];
        }
      }
      marginalia.forEach(function(marginalis) {
        var annotations = marginalis.get("annotations");

        annotations.add(new Annotation({
          content: content,
          uuid: ux_uuid,
          sessionStart: startTime,
          createdAt: new Date(),
          elapsedTime: Math.abs(startTime - new Date())
        }));
      });
      $.ajax({
            url: '/savemarginalia/'+report_uuid+'/'+pdf_uuid+'/'+ux_uuid,
            type: "POST",
            data: {data:JSON.stringify({marginalia: self.toJSON()})},
            success: function(data) {
              //alert(data.toSource());
            },
            error: function(err) {
              alert('Error on saving!');
            }
          });
    }
  });

  return Marginalia;
});
