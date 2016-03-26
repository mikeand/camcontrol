(function() {
  "use strict";

  var cameraIP = 'http://10.1.1.5:8000'

  function camControlService($http) {

    function getCameraStatus() {
      return $http.get(cameraIP + '/motion/');
    }

    function setCameraStatus(enabled) {
      var data = { enabled: enabled };
      return $http.post(cameraIP + '/motion/', data);
    }

    return {
      'getCameraStatus': getCameraStatus,
      'setCameraStatus': setCameraStatus
    };
  }

  angular.module('starter.services')
    .factory('CameraControlService', ['$http', camControlService]);

}());
