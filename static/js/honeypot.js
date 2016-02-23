var app = angular.module('honeypotApp', ['ngRoute', 'ngAnimate', 'ui.bootstrap']);

app.config(function ($routeProvider) {
    $routeProvider.when('/', {
        templateUrl: "/snippets/home.html"
    }).when('/:templatePath', {
        template: '<ng-include src="templatePath" />',
        controller: 'CatchAllCtrl'
    });
});

app.controller("CatchAllCtrl", function ($scope, $routeParams) {
    $scope.templatePath = "snippets/" + $routeParams.templatePath + ".html";
});

app.controller("HeaderController", function($rootScope, $scope, $http) {
    console.log("Header");
    $http.get("/api/get_client_id").success(function(data) {
        $scope.client_id = data;
    });
    $http.get("/api/get_user_info").success(function(data) {
        if(data.status == "ok") {
            $rootScope.user = data.user;
        }
    });
    $scope.logout = function () {
        $http.post("/api/logout", null).success(function (data) {
            $rootScope.user = null;
            $location.path("/");
        });
    };
});