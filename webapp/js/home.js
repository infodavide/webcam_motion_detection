/* methods prefixed by '_' can be considered as private or protected (called by the other methods of the object or by html handler defined by this class */
class HomeController{
  /* constructor */
  constructor(){
    console.log('Initialization of HomeController...');
    const obj=this;
    var path=BASE_URL+'/templates/home.html';
    $.ajax({
        url:path,
        cache:HANDLEBARS_CACHE,
        success:function(data){
            var templateInput={ controller : obj };
            var template=Handlebars.compile(data,{ strict: true });
            $('#content').html(template(templateInput));
            $('#video').attr('src',BASE_URL+'/video?='+new Date().getTime());
        }
    });
    console.log('HomeController initialized');
  }
}