/* methods prefixed by '_' can be considered as private or protected (called by the other methods of the object or by html handler defined by this class */
class DetectionPeriodsController{
  static to2Digits(value){
    var result='00';
    if(isValid(value)){
      result=value.toString();
      if (result.length==1){
        result='0'+result;
      }
    }
    return result;
  }
  static buildHoursInputOptions(fieldId,required,disabled){
    var result=buildInputOptions(fieldId,'select',required,disabled);
    result.items=[];
    for(var i=0;i<24;i++){
      const v=DetectionPeriodsController.to2Digits(i);
      result.items.push(buildSelectOption(v,v));
    }
    return result;
  }
  static buildMinutesInputOptions(fieldId,required,disabled){
    var result=buildInputOptions(fieldId,'select',required,disabled);
    result.items=[];
    for(var i=0;i<60;i++){
      const v=DetectionPeriodsController.to2Digits(i);
      result.items.push(buildSelectOption(v,v));
    }
    return result;
  }
  static buildWeekdayInputOptions(fieldId,required,disabled){
    var result=buildInputOptions(fieldId,'select',required,disabled);
    result.items=[];
    result.items.push(buildSelectOption(1,$.i18n('monday')));
    result.items.push(buildSelectOption(2,$.i18n('tuesday')));
    result.items.push(buildSelectOption(3,$.i18n('wednesday')));
    result.items.push(buildSelectOption(4,$.i18n('thursday')));
    result.items.push(buildSelectOption(5,$.i18n('friday')));
    result.items.push(buildSelectOption(6,$.i18n('saturday')));
    result.items.push(buildSelectOption(0,$.i18n('sunday')));
    return result;
  }
  static hashCode(value){
    var result=0;
    for(var i=0;i<value.length;i++){
      var character=value.charCodeAt(i);
      result=((result<<5)-result)+character;
      result=result&result; // Convert to 32bit integer
    }
    return result;
  }
  /* constructor */
  constructor(){
    console.log('Initialization of DetectionPeriodsController...');
    this._values=[];
    const obj=this;
    var path=BASE_URL+'/templates/detection_periods.html';
    isAdmin=true;
    $.ajax({
        url:path,
        cache:HANDLEBARS_CACHE,
        success:function(data){
            var templateInput={ controller : obj, values : obj._values };
            var template=Handlebars.compile(data,{ strict: true });
            $('#content').html(template(templateInput));
            obj._get();
        }
    });
    console.log('DetectionPeriodsController initialized');
  }
  getResourceKey(){
    return 'periods';
  }
  _showValues(){
    var templateInput={ controller : this };
    $('#periods_values').html(Handlebars.partials['detection_periods_values-partial'](templateInput));
  }
  _remove(id){
    if(!isAdmin){
      return;
    }
    if(!isValid(id)){
      // console.log('Cannot remove, id is not valid');
      return;
    }
    delete this._values[id];
    this._showValues();
  }
  _add(day,start,stop){
    if(!isAdmin){
      return;
    }
    day=parseInt($('#period_day').val());
    start=$('#period_start_h').val()+':'+$('#period_start_m').val();
    stop=$('#period_stop_h').val()+':'+$('#period_stop_m').val();
    if(isValid(day)&&isValid(start)&&isValid(stop)){
      var item={};
      item.day=day;
      item.start=start;
      item.stop=stop;
      this._values.push(item);
    }
    this._showValues();
  }
  _cancel(){
    this._get();
  }
  _get(){
    const obj=this;
    console.log('Retrieving periods...');
    this._values=[];
    jQuery.ajax({
      type:'GET',
      url:REST_BASE_URL+'/'+obj.getResourceKey(),
      dataType:'json',
      async:true,
      accept:'application/json',
      success:function(response){
        // console.log("Response: "+JSON.stringify(response));
        if(isValid(response)){
          obj._values=response;
        }
      },
      error:function(x,status,error){
        handleAjaxError(x,status,error);
      },
      complete:function(){
        obj._showValues();
      }
    });
  }
  _save(){
    if(!isAdmin){
      return;
    }
    const obj=this;
    var json;
    if(isValid(this._values)){
      json=JSON.stringify(this._values);
    }else{
      json='{ }';
    }
    // console.log('JSON: '+json);
    jQuery.ajax({
      type:"POST",
      url:REST_BASE_URL+'/'+obj.getResourceKey(),
      async:true,
      contentType:'application/json',
      dataType: 'json',
      data:json,
      success:function(response){
        // console.log("Response: "+JSON.stringify(response));
      },
      error:function(x){
        handleValidationError(obj.getResourceKey(),x);
      }
    });
  }
}
Handlebars.registerHelper('intToWeekday',function(value){
  if(typeof value==='object'&&value.fn){
    switch(value.fn(this)){
      case 1:
      case '1':
        return $.i18n('monday');
      case 2:
      case '2':
        return $.i18n('tuesday');
      case 3:
      case '3':
        return $.i18n('wednesday');
      case 4:
      case '4':
        return $.i18n('thursday');
      case 5:
      case '5':
        return $.i18n('friday');
      case 6:
      case '6':
        return $.i18n('saturday');
    }
  }
  return $.i18n('sunday');
});