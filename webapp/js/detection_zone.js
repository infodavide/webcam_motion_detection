/* methods prefixed by '_' can be considered as private or protected (called by the other methods of the object or by html handler defined by this class */
class DetectionZoneController{
  /* initialize the main view */
  init(){
    console.log('Initialization of DetectionZoneController...');
    content='<div id="video_div"><img id="video_frame" class="video" src="'+BASE_URL+'/frame"/></div>';
    $('#content').html(content);
    $('#video_frame').Jcrop({
        onChange: showCoords,
        onSelect: showCoords
    });
  }
}
function showCoords(coord){
  console.log('x='+ coord.x +' y='+ coord.y +' x2='+ coord.x2 +' y2='+ coord.y2);
  console.log('w='+coord.w +' h='+ coord.h);
};

const detectionZoneController=new DetectionZoneController();