/* -*- tab-width: 2; indent-tabs-mode: nil; c-basic-offset: 2; js-indent-level: 2; -*- */
define(function (require) {
  'use strict';
  var React = require("react");
  var _ = require("underscore");

  var Document = require("jsx!../spa/components/document");
  var Marginalia = require("jsx!../spa/components/marginalia");


  var DocumentView = React.createClass({
    componentDidMount: function() {
      var self = this;
      var marginaliaModel = this.props.marginalia;
      var documentModel = this.props.document;

      // Dispatch logic
      // Listen to model change callbacks -> trigger updates to components
      marginaliaModel.on("all", function(e, obj) {
        switch(e) {
        case "reset":
          documentModel.annotate(marginaliaModel.getActive());
          self.forceUpdate();
          break;
        case "annotations:change":
          break;
        case "change:active":
        case "annotations:add":
        case "annotations:remove":
          documentModel.annotate(marginaliaModel.getActive());
          documentModel.rr_annotate(marginaliaModel);
          self.forceUpdate();
          break;
        case "annotations:select":
          self.forceUpdate();
          break;
        default:
          break;
        }
      });

      documentModel.on("all", function(e, obj) {
        switch(e) {
        case "change:raw":
          self.forceUpdate();
          break;
        case "pages:change:state":
          if(obj.get("state") === window.RenderingStates.HAS_CONTENT) {
            documentModel.annotate(marginaliaModel.getActive());
          }
          self.forceUpdate();
          break;
        case "pages:ready":
          documentModel.annotate(marginaliaModel.getActive());
          self.forceUpdate();
          break;
        default:
          break;
        }
      });
    },
    componentWillUnmount: function() {
      var marginaliaModel = this.props.marginalia;
      var documentModel = this.props.document;

      marginaliaModel.off("all");
      documentModel.off("all");
    },
    endSession: function() {
      var documentModel = this.props.document;
      documentModel.submit_time(this.props.next_link);
    },
    render: function() {
      var self = this;
      var marginaliaModel = this.props.marginalia;
      var documentModel = this.props.document;
      var isEditable = this.props.isEditable;
      var record = this.props.time_spent;
      //alert(record);

      var hours = Math.floor(record / 3600);
      var minutes = Math.floor((record - (hours * 3600)) / 60);
      var seconds = record - (hours * 3600) - (minutes * 60);

      if(hours < 10){ hours = '0' + hours;}
      if(minutes < 10){ minutes = '0' + minutes;}
      if(seconds < 10){ seconds = '0' + seconds;}

      return(
          <div>
            <Document id="viewer" pdf={documentModel} marginalia={marginaliaModel} isEditable={isEditable} />
            <div id="side">
              <button href="#" className="button" onClick={this.endSession}>Next</button><span id="timer"><span id="hh">{hours}</span><span id="mm">{minutes}</span><span id="ss">{seconds}</span></span>
              <Marginalia marginalia={marginaliaModel} isEditable={isEditable} />
            </div>
          </div>
      );
    }
  });

  return DocumentView;
});
