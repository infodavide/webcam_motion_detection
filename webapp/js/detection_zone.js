/* methods prefixed by '_' can be considered as private or protected (called by the other methods of the object or by html handler defined by this class */
class DetectionZoneController{
  /* constructor */
  constructor(){
    console.log('Initialization of DetectionZoneController...');
    this._zone=undefined;
    this._jcrop_api=undefined
    const obj=this;
    var path=BASE_URL+'/templates/detection_zone.html';
    $.ajax({
        url:path,
        cache:HANDLEBARS_CACHE,
        success:function(data){
            var templateInput={ controller : obj };
            var template=Handlebars.compile(data,{ strict: true });
            $('#content').html(template(templateInput));
            $('#video_frame').Jcrop({
                    bgColor: '#ffffff',
                    bgOpacity: 0.4,
                    onChange: obj._setCoordinates
                },function(){
                obj._jcrop_api=this;
                if(isAdmin){
                    obj._jcrop_api.enable();
                }else{
                    obj._jcrop_api.disable();
                }
                obj._get();
                $('#video_frame').attr('src',BASE_URL+'/frame?='+new Date().getTime());
            });
        }
    });
    console.log('DetectionZoneController initialized');
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