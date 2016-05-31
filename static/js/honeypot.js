var app = angular.module('honeypotApp', ['ngRoute', 'ngAnimate', 'ngMaterial', 'ngMessages', 'ng-showdown', 'mdColorPicker', 'crumble']);

app.factory('Page', function () {
    var title = 'Honeypot';
    return {
        title: function () {
            return title;
        },
        setTitle: function (newTitle) {
            title = newTitle + " - Honeypot"
        }
    };
});

app.config(function ($routeProvider, $mdThemingProvider) {
    $routeProvider.when('/', {
        templateUrl: "/snippets/home.html",
        controller: 'HomeController',
        label: "Home"
    }).when('/project/:project_id', {
        template: '<ng-include src="\'snippets/project.html\'">',
        controller: 'ProjectController',
        label: '{{project_title}}', // title of the project
        parent: '/projects'
    }).when('/project/:project_id/milestones', {
        template: '<ng-include src="\'snippets/milestones.html\'">',
        controller: 'MilestonesController',
        label: 'Milestones'
    }).when('/project/:project_id/milestone/:milestone_id', {
        template: '<ng-include src="\'snippets/milestone.html\'">',
        controller: 'MilestoneController',
        label: '{{third_level}}', // title of the milestone
        parent_to_replace: '/project/%id%/milestones',
        regex_search: 'project',
        dynamic_parent: true
    }).when('/project/:project_id/todo/:todo_id', {
        template: '<ng-include src="\'snippets/todo.html\'">',
        controller: 'TodoController',
        label: '{{third_level}}', // title of the todo
        parent_to_replace: '/project/%id%',
        regex_search: 'project',
        dynamic_parent: true
    }).when('/:templatePath', {
        template: '<ng-include src="templatePath">',
        controller: 'CatchAllCtrl',
        label: '{{lowest_title}}', // lowest (catchall)
        parent: '/'
    });

    $mdThemingProvider.theme('default').primaryPalette('blue-grey', {
        'default': '800', // by default use shade 800 from the blue-grey palette for primary intentions
        //'hue-1': '100', // use shade 100 for the <code>md-hue-1</code> class
        //'hue-2': '600', // use shade 600 for the <code>md-hue-2</code> class
        //'hue-3': '300' // use shade A100 for the <code>md-hue-3</code> class
    }).accentPalette('orange', {
        'default': '500' // use shade 500 for default, and keep all other shades the same
    });
});

app.controller("TitleController", function ($scope, Page) {
    $scope.Page = Page;
});

app.controller("HomeController", function (crumble, Page) {
    crumble.update();
    Page.setTitle("Home");
});

app.controller('AppCtrl', function ($scope, $timeout, $mdSidenav, $log, crumble) {
    $scope.crumble = crumble;

    var getParent = crumble.getParent;
    crumble.getParent = function (path) {
        var route = crumble.getRoute(path);
        if (route != undefined && angular.isDefined(route.dynamic_parent) && angular.isDefined(route.regex_search) && angular.isDefined(route.parent_to_replace)) {
            console.log("DYNAMIC PARENT!!!");
            var searchregex_str = "\/" + route.regex_search + "\/(.*?)\/";
            var searchregex = new RegExp(searchregex_str, "g");
            var id = searchregex.exec(path)[1];
            if (id == -1) { // if not found
                console.log("search found nothing");
                return "/"
            }
            var realparent = route.parent_to_replace.replace("%id%", id);
            console.log(realparent);
            console.log("end dynamic parent");
            return realparent;
        }
        return route && angular.isDefined(route.parent) ? route.parent : getParent(path);
    };

    var update = crumble.update;
    crumble.update = function (context) {
        update(context);
        crumble.trail.shift();
    };


    $scope.toggleLeft = buildDelayedToggler('left');
    /**
     * Supplies a function that will continue to operate until the
     * time is up.
     */
    function debounce(func, wait, context) {
        var timer;
        return function debounced() {
            var context = $scope,
                args = Array.prototype.slice.call(arguments);
            $timeout.cancel(timer);
            timer = $timeout(function () {
                timer = undefined;
                func.apply(context, args);
            }, wait || 10);
        };
    }

    /**
     * Build handler to open/close a SideNav; when animation finishes
     * report completion in console
     */
    function buildDelayedToggler(navID) {
        return debounce(function () {
            $mdSidenav(navID)
                .toggle()
                .then(function () {
                    $log.debug("toggle " + navID + " is done");
                });
        }, 200);
    }

    function buildToggler(navID) {
        return function () {
            $mdSidenav(navID)
                .toggle()
                .then(function () {
                    $log.debug("toggle " + navID + " is done");
                });
        }
    }
});

app.controller('LeftCtrl', function ($scope, $timeout, $mdSidenav) {
    $scope.close = function () {
        $mdSidenav('left').close();
    };
});


/* Luca's stuff */
/*--------------*/
app.controller("CatchAllCtrl", function ($scope, $rootScope, $routeParams, crumble, Page) {
    console.log("CatchAll");
    $scope.templatePath = "snippets/" + $routeParams.templatePath + ".html";
    crumble.update({lowest_title: $routeParams.templatePath});
    Page.setTitle($rootScope.title_dict[$routeParams.templatePath]);
});

app.controller("HeaderController", function ($rootScope, $scope, $http, $location, $mdDialog, crumble) {
    $rootScope.status_strings = ["Open", "Closed"];
    $rootScope.title_dict = {};
    $rootScope.title_dict["labels"] = "Labels";
    $rootScope.title_dict["projects"] = "Projects";
    $http.get("/api/get_client_id").success(function (data) {
        $scope.client_id = data;
        $scope.github_login_url = "https://github.com/login/oauth/authorize?scope=user:email&client_id=" + data;
    });
    $http.get("/api/get_user_info").success(function (data) {
        if (data.status == "ok") {
            $rootScope.user = data.user;
        }
    });
    $http.get("/api/get_users").success(function (data) {
        if (data.status == "error") {
            console.log("not authorized");
            return;
        }
        var arr = {};
        data.forEach(function (value) {
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
    };
    $rootScope.test_a = function () {
        console.log(crumble.trail);
        console.log($location.path());
    };
    $rootScope.handle_crumble = function (current_project_id, third_level, new_project_name, new_project_id) {
        console.log("handle_crumble()");
        $rootScope.third_level = third_level;
        if (new_project_name && new_project_id) { // handle project name & id
            console.log("already given project parameters");
            $rootScope.project = {id: new_project_id, title: new_project_name};
        } else if ($rootScope.project == undefined || current_project_id != $rootScope.project.id) {
            $rootScope.update_project_name(current_project_id, true);
            return;
        }
        handle_crumble_continue();
    };
    var handle_crumble_continue = function () {
        // handle lowest label
        var lowest = /\/(.*?)\//.exec($location.path())[1];
        if (lowest == undefined) {
            lowest = /\/(.*)/.exec($location.path())[1];
        }
        if (lowest == "project" || lowest == "projects") {
            $rootScope.title_2 = "Projects";
        }
        else if (lowest == "labels" || lowest == "label") {
            $rootScope.title_2 = "Labels"
        }
        console.log($rootScope.project.title);
        console.log($rootScope.title_2);
        crumble.update({
            project_title: $rootScope.project.title,
            lowest_title: $rootScope.title_2,
            third_level: $rootScope.third_level
        });
    };
    $rootScope.update_project_name = function (project_id, continueafterwards) {
        $http.get("/api/get_project", {params: {project_id: project_id}}).success(function (data) {
            console.log("updated project name");
            $rootScope.project = {id: project_id, title: data.title};
            if (continueafterwards) {
                handle_crumble_continue();
            }
        });
    };
    $rootScope.showConfirm = function (title, content, callback, ev) {
        console.log("arguments[4]");
        console.log(arguments[4]);
        var extra_param = arguments[4];
        var confirm = $mdDialog.confirm()
            .title(title)
            .textContent(content)
            .targetEvent(ev)
            .ok('Confirm')
            .cancel('Cancel');
        $mdDialog.show(confirm).then(function () {
            callback(true, extra_param);
        }, function () {
            callback(false);
        });
    };
});

app.controller("ProjectsController", function ($scope, $http, $mdDialog, $mdMedia) {
    $http.get("/api/get_projects").success(function (data) {
        console.log(data);
        $scope.projects = data;
    });
    $scope.add_project = function (ev) {
        // Modal add dialog
        $scope.customFullscreen = $mdMedia('xs') || $mdMedia('sm');
        var useFullScreen = ($mdMedia('sm') || $mdMedia('xs')) && $scope.customFullscreen;
        $mdDialog.show({
            controller: AddProjectController,
            templateUrl: 'snippets/add_project.html',
            parent: angular.element(document.body),
            targetEvent: ev,
            clickOutsideToClose: true,
            fullscreen: useFullScreen,
            locals: {projects: $scope.projects, fullscreen: useFullScreen}
        });
        $scope.$watch(function () {
            return $mdMedia('xs') || $mdMedia('sm');
        }, function (wantsFullScreen) {
            console.log("wantsFullScreen:");
            console.log(wantsFullScreen);
            $scope.customFullscreen = (wantsFullScreen === true);
        });
    };
    function AddProjectController($scope, $http, projects, fullscreen) {
        $scope.fullscreen = fullscreen;
        console.log("addprojectcontroller");
        console.log($scope.fullscreen);
        $scope.cancel = function () {
            $mdDialog.hide()
        };
        $scope.submit = function (title, description) {
            if (description == undefined) {
                description = "";
            }
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

app.controller("ProjectController", function ($scope, $routeParams, $http, $mdMedia, $mdDialog, $location, $rootScope, Page) {
    $scope.id = $routeParams.project_id;
    $http.get("/api/get_project", {params: {project_id: $routeParams.project_id}}).success(function (data) {
        Page.setTitle(data.title);
        $rootScope.handle_crumble($scope.id, undefined, data.title, $scope.id);
        $scope.project = data;
        console.log(data);
    });
    $http.get("/api/get_todos", {params: {project_id: $routeParams.project_id}}).success(function (data) {
        console.log(data);
        $scope.todos = data;
    });
    $scope.add_todo = function (ev) {
        // Modal add dialog
        $scope.customFullscreen = $mdMedia('xs') || $mdMedia('sm');
        var useFullScreen = ($mdMedia('sm') || $mdMedia('xs')) && $scope.customFullscreen;
        $mdDialog.show({
            controller: AddTodoController,
            templateUrl: 'snippets/add_todo.html',
            parent: angular.element(document.body),
            targetEvent: ev,
            clickOutsideToClose: true,
            fullscreen: useFullScreen,
            locals: {todos: $scope.todos, project_id: $scope.project.id, fullscreen: useFullScreen}
        });
        $scope.$watch(function () {
            return $mdMedia('xs') || $mdMedia('sm');
        }, function (wantsFullScreen) {
            $scope.customFullscreen = (wantsFullScreen === true);
        });
    };
    $scope.remove_project = function (confirm) {
        console.log("REMOVE PROJECT: " + confirm);
        if (confirm === false) return;
        $http.post("/api/remove_project", {project_id: $scope.id}).success(function (data) {
            console.log(data);
            if (data.status == "ok") {
                $location.path("/projects");
            } else {
                alert("Error while removing project!");
            }
        });
    };
    function AddTodoController($scope, $http, todos, project_id, fullscreen) {
        $scope.fullscreen = fullscreen;
        console.log("addtodocontroller");
        $scope.cancel = function () {
            $mdDialog.hide()
        };
        $scope.submit = function (title, description, assignee, milestone) {
            console.log(title + " - " + description + " - " + assignee + " - " + milestone);
            if (description == null) description = "";

            $http.post("/api/add_todo", {
                "title": title,
                "description": description,
                "assignee": assignee,
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
        //$scope.get_users
        $scope.get_users = function (name) {
            var parameters;
            if (name.length <= 1) {
                parameters = {};
            } else {
                parameters = {params: {name: name}};
            }
            console.log("get_users - " + name);
            console.log("Selected: " + $scope.selectedItem); // title description assignee milestone
            $http.get("/api/get_users", parameters).success(function (data) {
                $scope.users_filtered = data;
                console.log(data);
            });
        };
        $scope.get_milestones = function (name) {
            console.log("get_milestones - " + name);
            $http.get("/api/get_milestones_by_name", {
                params: {
                    name: name,
                    project_id: project_id
                }
            }).success(function (data) {
                $scope.milestones = data;
                console.log(data);
            });
        }
    }
});

app.controller("TodoController", function ($scope, $rootScope, $routeParams, $http, Page) {
    $scope.id = $routeParams.todo_id;
    $scope.project_id = $routeParams.project_id;
    // $scope.update_status_texts = ["Close todo", "Re-open todo"];
    $http.get("/api/get_todo_detail", {params: {id: $routeParams.todo_id}}).success(function (data) {
        Page.setTitle(data.title);
        $rootScope.handle_crumble($scope.project_id, data.title);
        console.log(data);
        // data.status = data.status == 1; // convert 0/1 to boolean
        $scope.todo = data;
        if($scope.todo.assignee == null) {
            $scope.todo.assignee_list = [];
        } else {
            $scope.todo.assignee_list = [$scope.todo.assignee];
        }
        console.log($scope.todo.assignee_list)
    });
    $http.get("/api/get_events", {params: {id: $scope.id}}).success(function (data) {
        console.log(data);
        $scope.events = data;
    });
    $http.get("/api/get_assigned_labels", {params: {id: $scope.id}}).success(function (data) {
        $scope.assigned_labels = data;
        console.log(data);
    });
    $http.get("/api/get_labels").success(function (data) {
        var arr = {};
        data.forEach(function (entry) {
            arr[entry.id] = entry;
        });
        $scope.labels = arr;
        $scope.labels_unsorted = data;
        console.log("labels: ");
        console.log($scope.labels);
    });
    $scope.update_status = function () {
        console.log("update status");
        var status = $scope.todo.status; //== true ? 1 : 0; // convert boolean to 0/1
        $http.post("/api/update_todo_status", {todo_id: $scope.id, status: status}).success(function (data) {
            console.log(data);
            if (data.status == "ok") {
                //$scope.todo.status = status == 1; // convert 0/1 to boolean
                $scope.events.push(data.new_event)
            }
        });
    };
    $scope.submit_comment = function (comment) {
        $http.post("/api/add_comment", {content: comment, todo_id: $scope.id}).success(function (data) {
            console.log(data);
            if (data.status == "ok") {
                $scope.events.push(data.new_comment);
            }
        });
    };
    //$scope.get_users
    $scope.get_users = function (name) {
        var parameters;
        if (name.length <= 1) {
            parameters = {};
        } else {
            parameters = {params: {name: name}};
        }
        console.log("get_users - " + name);
        console.log("Selected: " + $scope.selectedItem); // title description assignee milestone
        $http.get("/api/get_users", parameters).success(function (data) {
            $scope.users_filtered = data;
            console.log(data);
        });
    };
    $scope.md_chips_to_id = function(chip) {
        return chip.id;
    };
    $scope.chip_add_label = function(label_id) {
        console.log("ADD LABEL!!!!");
        $http.post("/api/add_label_to_todo", {label_id: label_id, todo_id: parseInt($scope.id)}).success(function(data) {
            console.log(data);
            if (data.status == "ok") {
                //$scope.todo.status = status == 1; // convert 0/1 to boolean
                $scope.events.push(data.new_event)
            }
        });
    };
    $scope.chip_remove_label = function(label_id) {
        console.log("REMOVE LABEL!!!!");
        $http.post("/api/remove_label_from_todo", {label_id: label_id, todo_id: parseInt($scope.id)}).success(function(data) {
            console.log(data);
            if (data.status == "ok") {
                //$scope.todo.status = status == 1; // convert 0/1 to boolean
                $scope.events.push(data.new_event)
            }
        });
    };
    $scope.chip_add_assignee = function(new_assignee) {
        console.log("ADD ASSIGNEE!!!!");
        $http.post("/api/update_todo_assignee", {todo_id: parseInt($scope.id), assignee: new_assignee}).success(function(data) {
            console.log(data);
            if (data.status == "ok") {
                //$scope.todo.status = status == 1; // convert 0/1 to boolean
                $scope.events.push(data.new_event)
            }
        });
    };
    $scope.chip_remove_assignee = function() {
        console.log("REMOVE ASSIGNEE!!!!");
        $http.post("/api/update_todo_assignee", {todo_id: parseInt($scope.id), assignee: null}).success(function(data) {
            console.log(data);
            if (data.status == "ok") {
                //$scope.todo.status = status == 1; // convert 0/1 to boolean
                $scope.events.push(data.new_event)
            }
        });
    }
});

app.controller("MilestonesController", function ($scope, $routeParams, $http, $mdMedia, $mdDialog, $rootScope, Page) {
    console.log("MilestonesController");
    $scope.project_id = $routeParams.project_id;
    Page.setTitle("Milestones");
    $rootScope.handle_crumble($scope.project_id);
    $http.get("/api/get_milestones", {params: {project_id: $scope.project_id}}).success(function (data) {
        console.log(data);
        $scope.milestones = data;
    });
    $scope.add_milestone = function (ev) {
        // Modal add dialog
        $scope.customFullscreen = $mdMedia('xs') || $mdMedia('sm');
        var useFullScreen = ($mdMedia('sm') || $mdMedia('xs')) && $scope.customFullscreen;
        $mdDialog.show({
            controller: AddMilestoneController,
            templateUrl: 'snippets/add_milestone.html',
            parent: angular.element(document.body),
            targetEvent: ev,
            clickOutsideToClose: true,
            fullscreen: useFullScreen,
            locals: {milestones: $scope.milestones, project_id: $scope.project_id, fullscreen: useFullScreen}
        });
        $scope.$watch(function () {
            return $mdMedia('xs') || $mdMedia('sm');
        }, function (wantsFullScreen) {
            $scope.customFullscreen = (wantsFullScreen === true);
        });
    };
    function AddMilestoneController($scope, $http, project_id, milestones, fullscreen) {
        console.log("addmilestonecontroller");
        $scope.fullscreen = fullscreen;

        $scope.submit = function (title, description, duedate) {
            if (title == null) {
                alert("Please enter a title!");
                return;
            }
            if (description == null) description = "";

            console.log(title + " - " + description + " - " + duedate);
            $http.post("/api/add_milestone", {
                "title": title,
                "description": description,
                "duedate": duedate,
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

app.controller("MilestoneController", function ($scope, $routeParams, $http, $location, $rootScope, Page) {
    $scope.project_id = $routeParams.project_id;
    $scope.milestone_id = $routeParams.milestone_id;
    $http.get("/api/get_milestone", {params: {milestone_id: $scope.milestone_id}}).success(function (data) {
        Page.setTitle(data.title);
        $rootScope.handle_crumble($scope.project_id, data.title);
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
    $scope.remove_milestone = function (confirm, milestone_id) {
        console.log("remove");
        if (confirm === false) return;
        $http.post("/api/remove_milestone", {milestone_id: milestone_id}).success(function (data) {
            console.log(data);
            if (data.status == "ok") {
                $location.path("/project/" + $scope.project_id + "/milestones");
            } else {
                alert("Error while removing!")
            }
        });
    };
});

app.controller("LabelController", function ($scope, $http, $mdMedia, $mdDialog) {
    console.log("labelcontroller");
    $http.get("/api/get_labels").success(function (data) {
        console.log(data);
        $scope.labels = data;
    });
    $scope.add_label = function (ev) {
        // Modal add dialog
        $scope.customFullscreen = $mdMedia('xs') || $mdMedia('sm');
        var useFullScreen = ($mdMedia('sm') || $mdMedia('xs')) && $scope.customFullscreen;
        $mdDialog.show({
            controller: AddLabelController,
            templateUrl: 'snippets/add_label.html',
            parent: angular.element(document.body),
            targetEvent: ev,
            clickOutsideToClose: true,
            fullscreen: useFullScreen,
            locals: {labels: $scope.labels, fullscreen: useFullScreen}
        });
        $scope.$watch(function () {
            return $mdMedia('xs') || $mdMedia('sm');
        }, function (wantsFullScreen) {
            $scope.customFullscreen = (wantsFullScreen === true);
        });
    };
    $scope.remove_label = function (confirm, label_id) {
        console.log("label_id: " + label_id);
        console.log(confirm);
        if (confirm === false) return;
        $http.post("/api/remove_label", {label_id: label_id}).success(function (data) {
            console.log(data);
            if (data.status == "ok") {
                $scope.labels.forEach(function (value, i) {
                    if (value.id == label_id) {
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
    function AddLabelController($scope, $http, labels, fullscreen) {
        $scope.fullscreen = fullscreen;
        console.log("addlabelcontroller");
        $scope.cancel = function () {
            $mdDialog.hide()
        };
        // $scope.update_color = function(hexstring) {
        //     if (/#\b[0-9A-F]{6}\b/gi.test(hexstring)) {
        //         $scope.valid_color = hexstring;
        //         console.log("valid color");
        //     } else {
        //         $scope.valid_color = "#000";
        //         console.log("invalid color")
        //     }
        // };
        $scope.submit = function (name, color) {
            $http.post("/api/add_label", {name: name, color: color}).success(function (data) {
                console.log(data);
                if (data.status == "ok") {
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
    if (monthname === undefined) {
        return "";
    }
    return monthname.substr(0, 3);
};
