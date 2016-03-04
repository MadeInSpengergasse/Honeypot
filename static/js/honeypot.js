var app = angular.module('honeypotApp', ['ngRoute', 'ngAnimate', 'ng-showdown', 'ngMaterial']);

app.config(function ($routeProvider) {
    $routeProvider.when('/', {
        templateUrl: "/snippets/home.html"
    }).when('/project/:project_id', {
        template: '<ng-include src="\'snippets/project.html\'">',
        controller: 'ProjectController'
    }).when('/project/:project_id/milestones', {
        template: '<ng-include src="\'snippets/milestones.html\'">',
        controller: 'MilestonesController'
    }).when('/project/:project_id/milestone/:milestone_id', {
        template: '<ng-include src="\'snippets/milestone.html\'">',
        controller: 'MilestoneController'
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

app.controller("HeaderController", function ($rootScope, $scope, $http, $location) {
    $rootScope.status_strings = ["Open", "Closed"];
    $http.get("/api/get_client_id").success(function (data) {
        $scope.client_id = data;
        $scope.github_login_url = "https://github.com/login/oauth/authorize?scope=user:email&client_id=" + data;
    });
    $http.get("/api/get_user_info").success(function (data) {
        if (data.status == "ok") {
            $rootScope.user = data.user;
        }
    });
    $scope.logout = function () {
        $http.post("/api/logout", null).success(function (data) {
            $rootScope.user = null;
            $location.path("/")
        });
    };
    $rootScope.href = function (url) {
        $location.path(url);
    };
    $rootScope.goto = function (url) {
        window.location.href = url;
    }
});

app.controller("ProjectsController", function ($scope, $http, $mdDialog, $mdMedia) {
    $http.get("/api/get_projects").success(function (data) {
        console.log(data);
        $scope.projects = data;
    });
    $scope.add_project = function (ev) {
        var useFullScreen = ($mdMedia('sm') || $mdMedia('xs')) && $scope.customFullscreen;
        $mdDialog.show({
                controller: AddProjectController,
                templateUrl: 'snippets/add_project.html',
                parent: angular.element(document.body),
                targetEvent: ev,
                clickOutsideToClose: true,
                fullscreen: useFullScreen,
                locals: {projects: $scope.projects}
            })
            .then(function (answer) {
                $scope.status = 'You said the information was "' + answer + '".';
            }, function () {
                $scope.status = 'You cancelled the dialog.';
            });
        $scope.$watch(function () {
            return $mdMedia('xs') || $mdMedia('sm');
        }, function (wantsFullScreen) {
            $scope.customFullscreen = (wantsFullScreen === true);
        });
    };
    function AddProjectController($scope, $http, projects) {
        console.log("addprojectcontroller");
        $scope.cancel = function () {
            $mdDialog.hide()
        };
        $scope.submit = function (title, description) {
            $http.post("/api/add_project", {"title": title, "description": description}).success(function (data) {
                console.log(data);
                if (data.status == "ok") {
                    projects.push({"title": title, "description": description, "status": 0, "id": data.id});
                    $mdDialog.hide()
                } else {
                    alert("Error while adding project.");
                }
            });
        }
    }
});

app.controller("ProjectController", function ($scope, $routeParams, $http, $mdMedia, $mdDialog) {
    $scope.id = $routeParams.project_id;
    $http.get("/api/get_project", {params: {project_id: $routeParams.project_id}}).success(function (data) {
        $scope.project = data;
    });
    $http.get("/api/get_todos", {params: {project_id: $routeParams.project_id}}).success(function (data) {
        console.log(data);
        $scope.todos = data;
    });
    $scope.add_todo = function (ev) {
        var useFullScreen = ($mdMedia('sm') || $mdMedia('xs')) && $scope.customFullscreen;
        $mdDialog.show({
            controller: AddTodoController,
            templateUrl: 'snippets/add_todo.html',
            parent: angular.element(document.body),
            targetEvent: ev,
            clickOutsideToClose: true,
            fullscreen: useFullScreen,
            locals: {todos: $scope.todos, project_id: $scope.project.id}
        });
        $scope.$watch(function () {
            return $mdMedia('xs') || $mdMedia('sm');
        }, function (wantsFullScreen) {
            $scope.customFullscreen = (wantsFullScreen === true);
        });
    };
    function AddTodoController($scope, $http, todos, project_id) {
        console.log("addtodocontroller");
        $scope.cancel = function () {
            $mdDialog.hide()
        };
        $scope.submit = function (title, description, asignee, milestone) {
            console.log(title + " - " + description + " - " + asignee + " - " + milestone);
            $http.post("/api/add_todo", {
                "title": title,
                "description": description,
                "asignee": asignee,
                "milestone": milestone,
                "project_id": project_id
            }).success(function (data) {
                console.log(data);
                if (data.status == "ok") {
                    todos.push({"title": title, "description": description, "status": 0, "id": data.id});
                    $mdDialog.hide()
                } else {
                    alert("Error while adding project.");
                }
            });
        };
        $scope.get_users = function (name) {
            console.log("get_users - " + name);
            console.log("Selected: " + $scope.selectedItem); // title description asignee milestone
            $http.get("/api/get_users", {params: {name: name}}).success(function (data) {
                $scope.users = data;
                console.log(data);
            });
        }
    }
});

app.controller("TodoController", function ($scope, $routeParams, $http) {
    $scope.id = $routeParams.todo_id;
    $scope.project_id = $routeParams.project_id;
    $http.get("/api/get_todo_detail", {params: {id: $routeParams.todo_id}}).success(function (data) {
        console.log(data);
        $scope.todo = data;
    });
});

app.controller("MilestonesController", function ($scope, $routeParams, $http) {
    console.log("MilestonesController");
    $scope.project_id = $routeParams.project_id;
    $http.get("/api/get_milestones", {params: {project_id: $scope.project_id}}).success(function (data) {
        console.log(data);
        $scope.milestones = data;

    });
});

app.controller("MilestoneController", function ($scope, $routeParams, $http) {
    $scope.project_id = $routeParams.project_id;
    $scope.milestone_id = $routeParams.milestone_id;
    $http.get("/api/get_milestone", {params: {milestone_id: $scope.milestone_id}}).success(function (data) {
        console.log(data);
        $scope.milestone = data;
    });
    $scope.timestamp_to_date = function (timestamp) {
        var date = new Date(timestamp);
        return date.getShortMonthName() + " " + date.getDate() + ", " + date.getFullYear();
    };
    $scope.timestamp_to_long_date = function(timestamp) {
        var date = new Date(timestamp);
        return date.getShortMonthName() + " " + date.getDate() + ", " + date.getFullYear() + ", " + ("0" + date.getUTCHours()).slice(-2) + ":" + ("0" + date.getUTCMinutes()).slice(-2);
    }
});

Date.prototype.monthNames = [
    "January", "February", "March",
    "April", "May", "June",
    "July", "August", "September",
    "October", "November", "December"
];

Date.prototype.getMonthName = function () {
    return this.monthNames[this.getMonth()];
};
Date.prototype.getShortMonthName = function () {
    return this.getMonthName().substr(0, 3);
};