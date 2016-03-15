var app = angular.module('honeypotApp', ['ngRoute', 'ngAnimate', 'ngMaterial', 'ngMessages', 'ng-showdown']);

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
    $http.get("/api/get_users").success(function(data) {
        var arr = [];
        data.forEach(function(value) {
            arr[value.id] = value;
        });
        $rootScope.users = arr;
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

app.controller("ProjectController", function ($scope, $routeParams, $http, $mdMedia, $mdDialog, $location) {
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
    $scope.remove_project = function() {
        $http.post("/api/remove_project", {project_id: $scope.id}).success(function(data) {
            console.log(data);
            if (data.status == "ok") {
                $location.path("/projects");
            } else {
                alert("Error while removing project!");
            }
        });
    };
    function AddTodoController($scope, $http, todos, project_id) {
        console.log("addtodocontroller");
        $scope.cancel = function () {
            $mdDialog.hide()
        };
        $scope.submit = function (title, description, asignee, milestone) {
            console.log(title + " - " + description + " - " + asignee + " - " + milestone);
            if(description == null) {
                description = "";
            }
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
                $scope.users_filtered = data;
                console.log(data);
            });
        };
        $scope.get_milestones = function(name) {
            console.log("get_milestones - " + name);
            $http.get("/api/get_milestones_by_name", {params: {name: name, project_id: project_id}}).success(function(data) {
                $scope.milestones = data;
                console.log(data);
            });
        }
    }
});

app.controller("TodoController", function ($scope, $routeParams, $http) {
    $scope.id = $routeParams.todo_id;
    $scope.project_id = $routeParams.project_id;
    $scope.update_status_texts = ["Close todo", "Re-open todo"];
    $http.get("/api/get_todo_detail", {params: {id: $routeParams.todo_id}}).success(function (data) {
        console.log(data);
        $scope.todo = data;
    });
    $http.get("/api/get_events", {params: {id: $scope.id}}).success(function(data) {
        console.log(data);
        $scope.events = data;
    });
    $http.get("/api/get_assigned_labels", {params: {id: $scope.id}}).success(function(data) {
        $scope.assigned_labels = data;
        console.log(data);
    });
    $http.get("/api/get_labels").success(function(data) {
        var arr = [];
        data.forEach(function(entry) {
            arr[entry.id] = entry;
        });
        $scope.labels = arr;
    });
    $scope.update_status = function() {
        console.log("update status");
        var status = $scope.todo.status == 0 ? 1 : 0;
        $http.post("/api/update_todo_status", {todo_id: $scope.id, status: status}).success(function(data) {
            console.log(data);
            if (data.status == "ok") {
                $scope.todo.status = status;
                $scope.events.push(data.new_event)
            }
        });
    };
    $scope.submit_comment = function(comment) {
        $http.post("/api/add_comment", {content: comment, todo_id: $scope.id}).success(function(data) {
            console.log(data);
            if(data.status == "ok") {
                comment = "";
                $scope.events.push(data.new_comment);
            }
        });
    }
});

app.controller("MilestonesController", function ($scope, $routeParams, $http, $mdMedia, $mdDialog) {
    console.log("MilestonesController");
    $scope.project_id = $routeParams.project_id;
    $http.get("/api/get_milestones", {params: {project_id: $scope.project_id}}).success(function (data) {
        console.log(data);
        $scope.milestones = data;
    });
    $scope.add_milestone = function (ev) {
        console.log("addmilestone");
        var useFullScreen = ($mdMedia('sm') || $mdMedia('xs')) && $scope.customFullscreen;
        $mdDialog.show({
            controller: AddMilestoneController,
            templateUrl: 'snippets/add_milestone.html',
            parent: angular.element(document.body),
            targetEvent: ev,
            clickOutsideToClose: true,
            fullscreen: useFullScreen,
            locals: {milestones: $scope.milestones, project_id: $scope.project_id}
        });
        $scope.$watch(function () {
            return $mdMedia('xs') || $mdMedia('sm');
        }, function (wantsFullScreen) {
            $scope.customFullscreen = (wantsFullScreen === true);
        });
    };
    function AddMilestoneController($scope, $http, project_id, milestones) {
        console.log("addmilestonecontroller");
        $scope.submit = function (title, description, startdate, enddate) {
            console.log(title + " - " + description + " - " + startdate + " - " + enddate);
            $http.post("/api/add_milestone", {
                "title": title,
                "description": description,
                "startdate": startdate,
                "enddate": enddate,
                "project_id": project_id
            }).success(function (data) {
                console.log(data);
                if (data.status == "ok") {
                    milestones.push({"title": title, "description": description, "status": 0, "id": data.id});
                    $mdDialog.hide()
                } else {
                    alert("Error while adding project.");
                }
            });
        };
        $scope.cancel = function () {
            $mdDialog.hide()
        };
    }
});

app.controller("MilestoneController", function ($scope, $routeParams, $http, $location) {
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
    $scope.timestamp_to_long_date = function (timestamp) {
        var date = new Date(timestamp);
        return date.getShortMonthName() + " " + date.getDate() + ", " + date.getFullYear() + ", " + ("0" + date.getUTCHours()).slice(-2) + ":" + ("0" + date.getUTCMinutes()).slice(-2);
    };
    $scope.remove_milestone = function() {
        console.log("remove");
        $http.post("/api/remove_milestone", {milestone_id: $scope.milestone_id}).success(function(data) {
            console.log(data);
            if (data.status == "ok") {
                $location.path("/project/"+$scope.project_id+"/milestones");
            } else {
                alert("Error while removing!")
            }
        });
    };
});

app.controller("LabelController", function($scope, $http, $mdMedia, $mdDialog) {
    console.log("labelcontroller");
    $http.get("/api/get_labels").success(function(data) {
        console.log(data);
        $scope.labels = data;
    });
    $scope.add_label = function (ev) {
        console.log("addmilestone");
        var useFullScreen = ($mdMedia('sm') || $mdMedia('xs')) && $scope.customFullscreen;
        $mdDialog.show({
            controller: AddLabelController,
            templateUrl: 'snippets/add_label.html',
            parent: angular.element(document.body),
            targetEvent: ev,
            clickOutsideToClose: true,
            fullscreen: useFullScreen,
            locals: {labels: $scope.labels}
        });
        $scope.$watch(function () {
            return $mdMedia('xs') || $mdMedia('sm');
        }, function (wantsFullScreen) {
            $scope.customFullscreen = (wantsFullScreen === true);
        });
    };
    $scope.remove_label = function(label_id) {
        console.log(label_id);
        $http.post("/api/remove_label", {label_id: label_id}).success(function(data) {
            console.log(data);
            if(data.status == "ok") {
                $scope.labels.forEach(function(value, i) {
                    if(value.id == label_id) {
                        $scope.labels.splice(i, 1);
                    }
                    console.log(i + " - " + value.id);
                    console.log(value)
                })
            } else {
                alert("error while removing label.")
            }

        });
    };
    function AddLabelController($scope, $http, labels) {
        console.log("addlabelcontroller");
        $scope.cancel = function () {
            $mdDialog.hide()
        };
        $scope.update_color = function(hexstring) {
            if (/#\b[0-9A-F]{6}\b/gi.test(hexstring)) {
                $scope.valid_color = hexstring;
                console.log("valid color");
            } else {
                $scope.valid_color = "#000";
                console.log("invalid color")
            }
        };
        $scope.submit = function(name, color) {
            $http.post("/api/add_label", {name: name, color: color}).success(function(data) {
                console.log(data);
                if(data.status == "ok") {
                    $mdDialog.hide();
                    labels.push({id: data.id, name: name, color: color})
                }
            });
        }
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
    var monthname = this.getMonthName();
    if(monthname === undefined) {
        return "";
    }
    return monthname.substr(0, 3);
};