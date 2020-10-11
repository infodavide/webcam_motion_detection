/* methods prefixed by '_' can be considered as private or protected (called by the other methods of the object or by html handler defined by this class */
class DetectionPeriodsController{
  static to2Digits(value){
    var result = '00';
    if(isValid(value)){
        result=value.toString();
        if (result.length==1){
            result='0'+result;
        }
    }
    return result;
  }
  static buildHoursInputOptions(fieldId,required,disabled){
    var options=buildInputOptions(fieldId,'select',required,disabled);
    options.items=[];
    for(var i=0;i<24;i++){
      const v=DetectionPeriodsController.to2Digits(i);
      options.items.push(buildSelectOption(v,v));
    }
    return options;
  }
  static buildMinutesInputOptions(fieldId,required,disabled){
    var options=buildInputOptions(fieldId,'select',required,disabled);
    options.items=[];
    for(var i=0;i<60;i++){
      const v=DetectionPeriodsController.to2Digits(i);
      options.items.push(buildSelectOption(v,v));
    }
    return options;
  }
  /* constructor */
  constructor(){
    console.log('Initialization of DetectionPeriodsController...');
    $('#content').html('<div id="periods_div"></div>');
    this._get();
  }
  getResourceKey(){
    return 'periods';
  }
  _showValues(values){
    var content='<div style="margin-top:16px;"><h1 data-i18n="periods"></h1><p data-i18n="periods_description"></p>';
    if(isAdmin){
      content+='<form id="periods_form" onsubmit="controller._save();return false;">';
    }
    content+='<div class="row row-header">';
    content+='<div class="column col-lg-2 col-header" data-i18n="weekday"></div>';
    content+='<div class="column col-lg-5 col-header" data-i18n="select_start_time"></div>';
    content+='<div class="column col-lg-5 col-header" data-i18n="select_stop_time"></div>';
    content+='</div>';
    content+=this._addWeekdayRow($.i18n('monday'),$.i18n('select_period_for_monday'),values[0],isAdmin,'mon');
    content+=this._addWeekdayRow($.i18n('tuesday'),$.i18n('select_period_for_tuesday'),values[1],isAdmin,'tue');
    content+=this._addWeekdayRow($.i18n('wednesday'),$.i18n('select_period_for_wednesday'),values[2],isAdmin,'wed');
    content+=this._addWeekdayRow($.i18n('thursday'),$.i18n('select_period_for_thursday'),values[3],isAdmin,'thu');
    content+=this._addWeekdayRow($.i18n('friday'),$.i18n('select_period_for_friday'),values[4],isAdmin,'fri');
    content+=this._addWeekdayRow($.i18n('saturday'),$.i18n('select_period_for_saturday'),values[5],isAdmin,'sat');
    content+=this._addWeekdayRow($.i18n('sunday'),$.i18n('select_period_for_sunday'),values[6],isAdmin,'sun');
    if(isAdmin){
      content+='<div style="margin-top:16px;">';
      content+='<button type="submit" id="btn_submit_periods" class="btn btn-primary mb-2" data-i18n="save"></button>';
      content+='<button id="btn_cancel_periods" class="btn btn-primary mb-2" onclick="controller._cancel();" data-i18n="cancel"></button>';
      content+='</div>';
      content+='</form>';
    }
    content+='</div>';
    $('#periods_div').html(content);
  }
  _addWeekdayRow(label,title,value,editable,day){
    var content='<div class="row">';
    content+='<div class="column col-lg-2" title="'+title+'">'+label+'</div>';
    content+='<div class="column col-lg-5" style="display:flex;" data-i18n="[title]select_start_time_of_detection">';
    var hoursOptions=DetectionPeriodsController.buildHoursInputOptions(day+'_s_h',true,!editable);
    var minutesOptions=DetectionPeriodsController.buildMinutesInputOptions(day+'_s_m',true,!editable);
    var v=value[0].split(':');
    content+=buildInput(title,v[0],hoursOptions);
    content+=buildInput(title,v[1],minutesOptions);
    content+='</div>';
    content+='<div class="column col-lg-5" style="display:flex;" data-i18n="[title]select_stop_time_of_detection">';
    hoursOptions=DetectionPeriodsController.buildHoursInputOptions(day+'_e_h',true,!editable);
    minutesOptions=DetectionPeriodsController.buildMinutesInputOptions(day+'_e_m',true,!editable);
    v=value[1].split(':');
    content+=buildInput(title,v[0],hoursOptions);
    content+=buildInput(title,v[1],minutesOptions);
    content+='</div>';
    content+='</div>';
    return content;
  }
  _cancel(){
    this._get();
  }
  _get(){
    const obj=this;
    jQuery.ajax({
      type:'GET',
      url:REST_BASE_URL+'/'+obj.getResourceKey(),
      dataType:'json',
      async:true,
      accept:'application/json',
      success:function(response){
        //console.log("Response: "+JSON.stringify(response));
        var values=[["0:0","0:0"],["0:0","0:0"],["0:0","0:0"],["0:0","0:0"],["0:0","0:0"],["0:0","0:0"],["0:0","0:0"]];
        if(isValid(response)||response.length!==7){
          values=response;
        }
        obj._showValues(values);
      },
      error:function(x,status,error){
        handleAjaxError(x,status,error);
      }
    });
  }
  _save(){
    if(!isAdmin){
      return;
    }
    const obj=this;
    var json='[';
    json+='["'+$('#mon_s_h').val()+':'+$('#mon_s_m').val()+'","'+$('#mon_e_h').val()+':'+$('#mon_e_m').val()+'"]';
    json+=',["'+$('#tue_s_h').val()+':'+$('#tue_s_m').val()+'","'+$('#tue_e_h').val()+':'+$('#tue_e_m').val()+'"]';
    json+=',["'+$('#wed_s_h').val()+':'+$('#wed_s_m').val()+'","'+$('#wed_e_h').val()+':'+$('#wed_e_m').val()+'"]';
    json+=',["'+$('#thu_s_h').val()+':'+$('#thu_s_m').val()+'","'+$('#thu_e_h').val()+':'+$('#thu_e_m').val()+'"]';
    json+=',["'+$('#fri_s_h').val()+':'+$('#fri_s_m').val()+'","'+$('#fri_e_h').val()+':'+$('#fri_e_m').val()+'"]';
    json+=',["'+$('#sat_s_h').val()+':'+$('#sat_s_m').val()+'","'+$('#sat_e_h').val()+':'+$('#sat_e_m').val()+'"]';
    json+=',["'+$('#sun_s_h').val()+':'+$('#sun_s_m').val()+'","'+$('#sun_e_h').val()+':'+$('#sun_e_m').val()+'"]';
    json+=']';
    //console.log('JSON: '+json);
    jQuery.ajax({
      type:"POST",
      url:REST_BASE_URL+'/'+obj.getResourceKey(),
      async:true,
      contentType:'application/json',
      dataType: 'json',
      data:json,
      success:function(response){
        //console.log("Response: "+JSON.stringify(response));
      },
      error:function(x){
        handleValidationError(obj.getResourceKey(),x);
      }
    });
  }
}