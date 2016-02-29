var app = angular.module('honeypotApp', ['ngRoute', 'ngAnimate', 'ui.bootstrap']);

app.config(function ($routeProvider) {
    $routeProvider.when('/', {
        templateUrl: "/snippets/home.html"
    }).when('/project/:project_id', {
        template: '<ng-include src="\'snippets/project.html\'">',
        controller: 'ProjectController'
    }).when('/project/:project_id/todo/:todo_id', {
        template: '<ng-include src="\'snippets/todo.html\'">',
        controller: 'TodoController'
    }).when('/:templatePath', {
        template: '<ng-include src="templatePath" />',
        controller: 'CatchAllCtrl'
    });
});

app.controller("CatchAllCtrl", function ($scope, $routeParams) {
    $scope.templatePath = "snippets/" + $routeParams.templatePath + ".html";
});

app.controller("HeaderController", function($rootScope, $scope, $http) {
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

app.controller("ProjectsController", function($scope, $http) {
    $http.get("/api/get_projects").success(function(data) {
        console.log(data);
        $scope.projects = data;
    });
});

app.controller("ProjectController", function($scope, $routeParams, $http) {
    $scope.id = $routeParams.project_id;
    $http.get("/api/get_todos", {params: {project_id: $routeParams.project_id}}).success(function(data) {
        console.log(data);
        $scope.todos = data;
    });
});

app.controller("TodoController", function($scope, $routeParams, $http/*, $showdown*/) {
    $scope.id = $routeParams.todo_id;
    $scope.project_id = $routeParams.project_id;
    $http.get("/api/get_todo_detail", {params: {id: $routeParams.todo_id}}).success(function(data) {
        console.log(data);
        $scope.todo = data;
        //$scope.markdown_description = $showdown.makeHtml(data.description);
    });
});