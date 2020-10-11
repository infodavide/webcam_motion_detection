/* methods prefixed by '_' can be considered as private or protected (called by the other methods of the object or by html handler defined by this class */
class DetectionPeriodsController{
  /* initialize the main view */
  init(){
    console.log('Initialization of DetectionPeriodsController...');
    content='TODO';
    $('#content').html(content);
  }
}
const detectionPeriodsController=new DetectionPeriodsController();