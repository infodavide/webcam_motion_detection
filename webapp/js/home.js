/* methods prefixed by '_' can be considered as private or protected (called by the other methods of the object or by html handler defined by this class */
class HomeController{
  /* initialize the main view */
  init(){
    console.log('Initialization of HomeController...');
    content='<div id="video"><img style="-webkit-user-select: none;" src="'+BASE_URL+'/video" width="1037" height="583"/></div>';
    $('#content').html(content);
  }
}
const homeController=new HomeController();