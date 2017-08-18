/* -*- mode: js2; tab-width: 2; indent-tabs-mode: nil; c-basic-offset: 2; js2-basic-offset: 2 -*- */

define(function (require) {
  'use strict';

  var Marked = require("marked");
  var React = require("react");

  var Editable = React.createClass({
    getInitialState: function() {
      return { editable: false };
    },
    edit: function() {
      this.setState({ editable: true});
    },
    submit: function(e) {
      this.setState({ editable: false });
      this.props.callback(this.refs.input.value);
      var obj = this.refs.input.parentNode.parentNode.parentNode.parentNode;
      var upd = $(obj).parent().children().index(obj) - 1;
      var upd_val = this.refs.input.value;
      var url = window.location.href.split('?');
      var url_parts = url[0].split("/");
      var documentId = url_parts[url_parts.length-1];
      var reportId = url_parts[url_parts.length-2];
      var query_str = url[1].split("&");
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
      var marginaliaUrl = "/marginalia/" + reportId + "/" + documentId + "?" + url[1];
      $.get(marginaliaUrl, function(data) {
        var marginalia = JSON.parse(data);
        marginalia[upd].description = upd_val;
        $.ajax({
            url: '/savemarginalia/'+reportId+'/'+documentId+'/'+ux_uuid,
            type: "POST",
            data: {data:JSON.stringify({marginalia: marginalia})},
            success: function(data) {
              //alert(data.toSource());
            },
            error: function(err) {
              //alert(err.toSource());
              alert('Error on saving!');
            }
          });
      });
      e.preventDefault();
    },
    componentDidUpdate: function() {
      if(this.state.editable) {
        this.refs.input.focus();
      }
    },
    render: function() {
      var content = this.props.content || "*Click to edit*";
      if(content.indexOf("**Overall risk of bias prediction**") == -1){
        content = "**Overall risk of bias prediction**: "+content;
      }
      if(this.state.editable) {
        return (
            <form className="row collapse">
              <div className="small-10 columns">
                <div className="row collapse">
                  <label className="small-8 column"><strong>Overall risk of bias prediction:</strong></label>
                  <select className="small-4 column" value={this.props.content.replace("**Overall risk of bias prediction**:","").trim()} ref="input" onChange={(e) => this.props.changeHandler(e.target.value)}>
                    <option value=""></option>
                    <option value="unclear">Unclear</option>
                    <option value="low">Low</option>
                    <option value="high">High</option>
                    </select>
                  </div>
                </div>
              <div className="small-2 columns">
                <button href="#" className="button postfix" onClick={this.submit}>Edit</button>
              </div>
            </form>
        );
      } else {
        return (
            <div className="editable" onClick={this.edit}>
              <div dangerouslySetInnerHTML={{__html: Marked(content)}}></div>
            </div>);
      }
    }
  });

  return Editable;

});
