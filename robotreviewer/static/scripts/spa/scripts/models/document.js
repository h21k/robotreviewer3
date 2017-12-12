/* -*- mode: js2; tab-width: 2; indent-tabs-mode: nil; c-basic-offset: 2; js2-basic-offset: 2 -*- */
define(function (require) {
  'use strict';

  var Q = require("Q");
  var _ = require("underscore");
  var Backbone = require("backbone");

  var quoteRegex = function(str) {
    return str.replace(/([.*+?^=!:${}()|\[\]\/\\])/g, "\\$1");
  };

  var TextSearcher = new (require("../vendor/dom-anchor-bitap/text_searcher"))();
  var RenderingStates = window.RenderingStates = {
    INITIAL: 0,
    RUNNING: 1,
    HAS_PAGE: 2,
    HAS_CONTENT: 3,
    FINISHED: 4
  };

  var Page = Backbone.Model.extend({
    defaults: {
      raw: null,
      content: null,
      state: RenderingStates.INITIAL,
      annotations: {}
    }
  });

  var Pages = Backbone.Collection.extend({
    model: Page,
    _buildAggregate: function() {
      this._aggregate = { totalLength: 0, nodes: [], pages: [], text: "" };
    },
    _appendAggregate: function(pageIndex, pageContent) {
      var totalLength = this._aggregate.totalLength;
      var offset = 0;
      var items = pageContent.items;
      for (var j = 0; j < items.length; j++) {
        var item = items[j];
        var str = item.str;
        var nextOffset = offset + str.length;
        var node = { pageIndex: pageIndex,
                     nodeIndex: j,
                     interval: { lower: totalLength + offset,
                                 upper: totalLength + nextOffset }};
        this._aggregate.text += (str + " ");
        offset = nextOffset + 1;
        this._aggregate.nodes.push(node);
      }
      this._aggregate.pages.push({ offset: totalLength, length: offset });
      this._aggregate.totalLength += offset;
    },
    _requestPage: function(model, pagePromise) {
      return pagePromise
        .then(function(raw) {
          model.set({
            raw: raw,
            state: RenderingStates.HAS_PAGE
          });
          return raw.getTextContent();
        })
        .then(function(content) {
          model.set({
            content: content,
            state: RenderingStates.HAS_CONTENT
          });
          return content;
        });
    },
    __matchCache: {},
    findMatch: function(annotation, text, useFuzzy) {
      var content = annotation.get("content");
      var prefix = annotation.get("prefix");
      var suffix = annotation.get("suffix");
      var len = text.length;
      // If no position is given, start in the middle of the document
      var position = annotation.get("position") || Math.floor(len / 2);

      var result = TextSearcher.searchExact(text, content);

      if(!result.matches.length) {
        var target = content
          .replace(/\s+/g, " ")
          .replace(/\s(\W)\s/g, "$1 ")
          .trim();
        var pattern = _.map(target.split(""), quoteRegex).join("\\W{0,3}");
        result = TextSearcher.searchRegex(text, pattern, false);
      }
      if(!result.matches.length && useFuzzy) {
        result = TextSearcher.searchFuzzyWithContext(
          text,
          prefix,
          suffix,
          content,
          position,
          position + content.length,
          false, {
            matchDistance: 500,
            contextMatchThreshold: 0.75,
            patternMatchThreshold: 0.75,
            flexContext: true
          });

        if(!result.matches.length) {
          result = TextSearcher.searchFuzzy(
            text,
            content,
            position,
            position + content.length,
            false);
        }
      }
      return result.matches[0];
    },
    annotate: function(annotation, color, useFuzzy) {
      var self = this;
      var aggregate = this._aggregate;
      if (!aggregate) {
        return [];
      }
      var text = aggregate.text;

      var match = null;
      var cacheKey = annotation.get("content");
      if(this.__matchCache[cacheKey]) {
        match = this.__matchCache[cacheKey]
      } else {
        var match = this.findMatch(annotation, text, useFuzzy);
        this.__matchCache[cacheKey] = match;
      }

      if(!match) {
        return [];
      } else {
        var lower = match.start;
        var upper = match.end;
        var mapping = [];
        var nodes = aggregate.nodes;
        var pages = aggregate.pages;
        var nrNodes = nodes.length;
        for(var i = 0; i < nrNodes; ++i) {
          var node = _.clone(nodes[i]);
          if(node.interval.lower < upper && lower < node.interval.upper) {
            var pageOffset = pages[node.pageIndex].offset;
            var interval = { lower: node.interval.lower - pageOffset,
                             upper: node.interval.upper - pageOffset};
            mapping.push(_.extend(node, { range: _.clone(interval),
                                          interval: _.clone(interval)}));
          }
        }
        if(!_.isEmpty(mapping)) {
          mapping[0].range.lower = lower - pages[mapping[0].pageIndex].offset;
          mapping[mapping.length - 1].range.upper = upper - pages[mapping[mapping.length - 1].pageIndex].offset;
        }

        return mapping.map(function(m) {
          m.color = color;
          m.uuid = annotation.get("uuid");
          return m;
        });
      }
    },
    populate: function(pdf) {
      var self  = this;

      this._buildAggregate();

      var pageQueue = _.range(0, pdf.numPages);
      var pages = _.map(pageQueue, function(pageNr) {
        return new Page();
      });
      this.reset(pages, {silent: true}); // set a bunch of empty pages

      var process = function(arr) {
        if(arr.length === 0) {
          self.trigger("ready");
          return;
        }
        var pageIndex = _.first(arr);
        var page = pages[pageIndex];
        page.set({state: RenderingStates.RUNNING});
        var p = self._requestPage(page, pdf.getPage(pageIndex + 1));
        p.then(function(content) {
          self._appendAggregate(pageIndex, content);
          process(_.rest(arr));
        });
      };

      process(pageQueue);
    }
  });

  var Document = Backbone.Model.extend({
    defaults: {
      text: "",
      fingerprint: null,
      state: RenderingStates.INITIAL,
      raw: null,
      binary: null,
      _cache: {}
    },
    initialize: function() {
      var self = this;
      var pages = new Pages();
      this._cache = {}; // clear
      this.set("pages", pages);
      pages.on("all", function(e, obj) {
        self.trigger("pages:" + e, obj);
      });
      pages.on("ready", function(e, obj) {
        self.set("state", RenderingStates.FINISHED);
      });
      setInterval(self.update_timer,1000);
    },
    update_timer: function() {
      var hours = parseInt($('#hh').text());
      var minutes = parseInt($('#mm').text());
      var seconds = parseInt($('#ss').text());

      seconds = seconds + 1;
      if(seconds == 60){
        minutes = minutes + 1;
        seconds = 0;
        if(minutes == 60){
          hours = hours + 1;
          minutes = 0;
        }
      }

      if(seconds<10){
        seconds = '0' + seconds;
      }
      if(minutes < 10){
        minutes = '0' + minutes;
      }
      if(hours < 10){
        hours = '0' + hours;
      }

      $('#timer').find('#hh').text(hours);
      $('#timer').find('#mm').text(minutes);
      $('#timer').find('#ss').text(seconds);
    },
    submit_time: function(link) {
      var hh = parseInt($('#hh').text());
      var mm = parseInt($('#mm').text());
      var ss = parseInt($('#ss').text());

      var time_spent = (hh * 3600) + (mm * 60) + ss;

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

      $.ajax({
        url: '/submit_time/'+report_uuid+'/'+pdf_uuid+'/'+ux_uuid,
        type: "POST",
        data: {data:time_spent},
        success: function(data) {
          if($('.block').find('form.collapse').length > 0){
            if(confirm('Have you finished editing the overall bias judgements (in the relevant Risk-of-Bias categories), and saved them? Click [CANCEL] to go back and check, or click [OK] to move to the next document.')){
              window.location.href = link;
            }
          }else{
            window.location.href = link;
          }
        },
        error: function(err) {
          //alert(err.toSource());
          alert('Error on saving!');
        }
      });
    },
    next_link: function() {
      var self = this;
      var url = window.location.href.split('?');
      var url_parts = url[0].split("/");
      var pdf_uuid = url_parts[url_parts.length-1];
      var report_uuid = url_parts[url_parts.length-2];

      $.ajax({
        url: '/get_next/'+pdf_uuid,
        type: "POST",
        async: false,
        success: function(data) {
          var response = JSON.parse(data);
          var url_parts = response.toString().split(",");
          var nextLink = '/#document/' + url_parts[0] + '/' + url_parts[1];
          return nextLink;
        }
      });
    },
    annotate: function(marginalia) {
      var self = this; // *sigh*
      var _cache = this.get("_cache");

      if(!marginalia) {
        self.get("pages").map(function(page, pageIndex) {
          page.set({annotations: []});
        });
        return;
      }

      var getAnnotationsPerPage = function(marginalia) {
        var mappings = [];

        marginalia.forEach(function(marginalis) {
          var color = marginalis.get("color");
          var annotations = marginalis.get("annotations");

          var m = _.flatten(annotations.map(function(annotation) {
            var cid = annotation.cid;
            if(_.size(_cache[cid])) {
              return _cache[cid];
            } else {
              var isFinished = self.get("state") === RenderingStates.FINISHED;
              var a = self.get("pages").annotate(annotation, color, isFinished);
              _cache[cid] = a;
              self.set("_cache", a);
              return a;
            }
          }));

          mappings.push.apply(mappings, m);
        });

        var result = {};
        mappings.forEach(function(mapping) {
          result[mapping.pageIndex] = result[mapping.pageIndex] || {};
          result[mapping.pageIndex][mapping.nodeIndex] =
            _.union(result[mapping.pageIndex][mapping.nodeIndex] || [], [mapping]);
        });
        return result;
      };

      var annotationsPerPage = getAnnotationsPerPage(marginalia);
      self.get("pages").map(function(page, pageIndex) {
        page.set({annotations: annotationsPerPage[pageIndex] || []});
      });
    },
    rr_annotate: function(marginalia){
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
      $.ajax({
        url: '/savemarginalia/'+report_uuid+'/'+pdf_uuid+'/'+ux_uuid,
        type: "POST",
        data: {data:JSON.stringify({marginalia : marginalia})},
        success: function(data) {
          //alert(data.toSource());
        },
        error: function(err) {
          //alert(err.toSource());
          alert('Error on saving!');
        }
      });
    },
    getText: function() {
      return this.get("pages")._aggregate.text;
    },
    loadFromUrl: function(url, uuid) {
      var self = this;
      self.set({binary: null, _cache: {}, scrollTo: uuid});
      PDFJS.getDocument(url).then(function(pdf) {
        self.set({raw: pdf,
                  fingerprint: pdf.pdfInfo.fingerprint,
                  state: RenderingStates.INITIAL});
        self.get("pages").populate(pdf);
      });
    },
    loadFromData: function(data, uuid) {
      var self = this;
      self.set({binary: data, _cache: {}, scrollTo: uuid});
      PDFJS.getDocument(data).then(function(pdf) {
        self.set({fingerprint: pdf.pdfInfo.fingerprint,
                  raw: data,
                  state: RenderingStates.INITIAL});
        self.get("pages").populate(pdf);
      });
    }
  });

  return Document;
});
