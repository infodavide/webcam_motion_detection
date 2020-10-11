/* methods prefixed by '_' can be considered as private or protected (called by the other methods of the object or by html handler defined by this class */
class DetectionZoneController{
  /* constructor */
  constructor(){
    console.log('Initialization of DetectionZoneController...');
    this._zone=undefined;
    this._jcrop_api=undefined
    const obj=this;
    var content='<div id="video_frame_div" class="center"><h1 data-i18n="zone"></h1><p data-i18n="zone_description"></p><img id="video_frame" class="video" style="-webkit-user-select: none;" src="'+BASE_URL+'/frame"/>';
    if(isAdmin){
      content+='<form id="coordinates_form" onsubmit="controller._save();return false;">';
      content+='<div style="margin-top:16px;">';
      content+='<button type="submit" id="btn_submit_coordinates" class="btn btn-primary mb-2" data-i18n="save"></button>';
      content+='<button id="btn_cancel_coordinates" class="btn btn-primary mb-2" onclick="controller._cancel();" data-i18n="cancel"></button>';
      content+='</div>';
      content+='</form>';
    }
    content+='</div>';
    $('#content').html(content);
    $('#video_frame').Jcrop({
      bgColor: '#ffffff',
      bgOpacity: 0.4,
      onChange: obj._setCoordinates
    },function(){
      obj._jcrop_api=this;
      obj._get();
      if(isAdmin){
        obj._jcrop_api.enable();
      }else{
        obj._jcrop_api.disable();
      }
    });
  }
  getResourceKey(){
    return 'coordinates';
  }
  _cancel(){
    this._get();
  }
  _setCoordinates(coord){
    if(!isAdmin){
      return;
    }
    const video_frame=$("#video_frame");
    const iw=video_frame.width();
    const ih=video_frame.height();
    // this not used inside a callback function
    controller._zone=[ Math.round((coord.x * 100)/iw), Math.round((coord.y * 100)/ih), Math.round((coord.x2 * 100)/iw), Math.round((coord.y2 * 100)/ih) ];
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
        if(!isValid(response)||response.x1==-1){
          this._zone=undefined;
          obj._jcrop_api.release();
        }else{
          this._zone=response;
          const video_frame=$("#video_frame");
          const iw=video_frame.width();
          const ih=video_frame.height();
          obj._zone=response;
          const selection=[response[0]*iw/100,response[1]*ih/100,response[2]*iw/100,response[3]*ih/100];
          obj._jcrop_api.setSelect(selection);
        }
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
    var json;
    if(isValid(this._zone)){
      json=JSON.stringify(this._zone);
    }else{
      json='[ -1, -1, -1, -1 ]';
    }
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