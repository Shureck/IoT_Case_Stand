	/*
	Вывод:
    	wb-msw-v3_21/Buzzer - пищалка (true/false)
        wb-mrgbw-d_78/RGB - RGB лента (255;255;255;)
        wb-mwac_68/K1 - открытие/закрытие крана (true/false)
        wb-mwac_68/K2 - контактор (true/false)
        НАДО ВЕНТИЛЯТОР

	Датчики:
    	wb-msw-v3_21/Current Motion - датчик движения
        wb-msw-v3_21/Illuminance - датчик освещенности
        wb-msw-v3_21/Sound Level - уровень звука
        wb-msw-v3_21/CO2 - уровень CO2
        wb-msw-v3_21/Humidity - влажность
        wb-msw-v3_21/Temperature - температура
*/

var delay=1000;
var i=0;
var array=[0,0,0];

setInterval(function(){
  if(array[i]>=255){
   i++;
    if(i>=3){
     i=0;
    }
    array=[0,0,0];
  }
  array[i]=array[i]+100;
  dev["wb-mrgbw-d_78"]["RGB"] = array.join(";");
},delay)

defineRule("water_fail_control", {
    whenChanged: "wb-msw-v3_21/Sound Level",
    then: function(newValue, devName, cellName) {
        // dev["wb-mrgbw-d_78"]["RGB"] = (newValue*5%255).toString()+";0;0;";

    }
})