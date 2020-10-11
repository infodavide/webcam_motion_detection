/* methods prefixed by '_' can be considered as private or protected (called by the other methods of the object or by html handler defined by this class */
class HomeController{
  /* constructor */
  constructor(){
    console.log('Initialization of HomeController...');
    var content='<div id="video_div"><p data-i18n="home_description"></p><img id="video_frame" class="video" style="-webkit-user-select: none;" src="'+BASE_URL+'/video"/></div>'
    $('#content').html(content);
  }
}