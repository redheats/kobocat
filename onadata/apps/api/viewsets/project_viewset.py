from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from onadata.libs.filters import AnonUserProjectFilter, ProjectOwnerFilter
from onadata.libs.mixins.labels_mixin import LabelsMixin
from onadata.libs.serializers.project_serializer import ProjectSerializer
from onadata.libs.serializers.share_project_serializer import \
    ShareProjectSerializer
from onadata.libs.serializers.xform_serializer import XFormSerializer
from onadata.apps.api.models import Project, ProjectXForm
from onadata.apps.api import tools as utils
from onadata.apps.api.permissions import ProjectPermissions
from onadata.apps.logger.models import XForm


class ProjectViewSet(LabelsMixin, ModelViewSet):
    """
List, Retrieve, Update, Create Project and Project Forms

Where:

- `pk` - is the project id
- `formid` - is the form id
- `owner` - is the username for the user or organization of the project

## Register a new Project
<pre class="prettyprint">
<b>POST</b> /api/v1/projects</pre>
> Example
>
>       {
>           "url": "https://ona.io/api/v1/projects/1",
>           "owner": "https://ona.io/api/v1/users/ona",
>           "name": "project 1",
>           "date_created": "2013-07-24T13:37:39Z",
>           "date_modified": "2013-07-24T13:37:39Z"
>       }

## List of Projects

<pre class="prettyprint"><b>GET</b> /api/v1/projects</pre>
> Example
>
>       curl -X GET https://ona.io/api/v1/projects

> Response
>
>       [
>           {
>               "url": "https://ona.io/api/v1/projects/1",
>               "owner": "https://ona.io/api/v1/users/ona",
>               "name": "project 1",
>               "date_created": "2013-07-24T13:37:39Z",
>               "date_modified": "2013-07-24T13:37:39Z"
>           },
>           {
>               "url": "https://ona.io/api/v1/projects/4",
>               "owner": "https://ona.io/api/v1/users/ona",
>               "name": "project 2",
>               "date_created": "2013-07-24T13:59:10Z",
>               "date_modified": "2013-07-24T13:59:10Z"
>           }, ...
>       ]

## List of Projects filter by owner/organization

<pre class="prettyprint">
<b>GET</b> /api/v1/projects?<code>owner</code>=<code>owner_username</code>
</pre>
> Example
>
>       curl -X GET https://ona.io/api/v1/projects?owner=ona

## Retrieve Project Information

<pre class="prettyprint">
<b>GET</b> /api/v1/projects/<code>{pk}</code></pre>
> Example
>
>       curl -X GET https://ona.io/api/v1/projects/1

> Response
>
>       {
>           "url": "https://ona.io/api/v1/projects/1",
>           "owner": "https://ona.io/api/v1/users/ona",
>           "name": "project 1",
>           "date_created": "2013-07-24T13:37:39Z",
>           "date_modified": "2013-07-24T13:37:39Z"
>       }

## Update Project Information

<pre class="prettyprint">
<b>PUT</b> /api/v1/projects/<code>{pk}</code> or \
<b>PATCH</b> /api/v1/projects/<code>{pk}</code></pre></pre>
> Example

>        curl -X PATCH -d 'metadata={"description": "Lorem ipsum",\
"location": "Nakuru, Kenya",\
"category": "water"}' \
https://ona.io/api/v1/projects/1

> Response
>
>       {
>           "url": "https://ona.io/api/v1/projects/1",
>           "owner": "https://ona.io/api/v1/users/ona",
>           "name": "project 1",
>           "metadata": {
>                        "description": "Lorem ipsum",
>                        "location": "Nakuru, Kenya",
>                        "category": "water"
>                        }
>           "date_created": "2013-07-24T13:37:39Z",
>           "date_modified": "2013-07-24T13:37:39Z"
>       }

## Share a project with a specific user

You can share a project with a specific user by `POST` a payload with

- `username` of the user you want to share the form with and
- `role` you want the user to have on the form. Available roles are `readonly`,
`dataentry`, `editor`, `manager`.

<pre class="prettyprint">
<b>POST</b> /api/v1/projects/<code>{pk}</code>/share
</pre>

> Example
>
>       curl -X POST -d username=alice -d role=readonly\
https://ona.io/api/v1/projects/1/share

> Response
>
>        HTTP 204 NO CONTENT

## Assign a form to a project
To [re]assign an existing form to a project you need to `POST` a payload of
`formid=FORMID` to the endpoint below.

<pre class="prettyprint">
<b>POST</b> /api/v1/projects/<code>{pk}</code>/forms</pre>
> Example
>
>       curl -X POST -d '{"formid": 28058}' \
https://ona.io/api/v1/projects/1/forms

> Response
>
>       {
>           "url": "https://ona.io/api/v1/forms/28058",
>           "formid": 28058,
>           "uuid": "853196d7d0a74bca9ecfadbf7e2f5c1f",
>           "id_string": "Birds",
>           "sms_id_string": "Birds",
>           "title": "Birds",
>           "allows_sms": false,
>           "bamboo_dataset": "",
>           "description": "",
>           "downloadable": true,
>           "encrypted": false,
>           "owner": "ona",
>           "public": false,
>           "public_data": false,
>           "date_created": "2013-07-25T14:14:22.892Z",
>           "date_modified": "2013-07-25T14:14:22.892Z"
>       }

## Upload XLSForm to a project

<pre class="prettyprint">
<b>POST</b> /api/v1/projects/<code>{pk}</code>/forms</pre>
> Example
>
>       curl -X POST -F xls_file=@/path/to/form.xls\
 https://ona.io/api/v1/projects/1/forms

> Response
>
>       {
>           "url": "https://ona.io/api/v1/forms/28058",
>           "formid": 28058,
>           "uuid": "853196d7d0a74bca9ecfadbf7e2f5c1f",
>           "id_string": "Birds",
>           "sms_id_string": "Birds",
>           "title": "Birds",
>           "allows_sms": false,
>           "bamboo_dataset": "",
>           "description": "",
>           "downloadable": true,
>           "encrypted": false,
>           "owner": "ona",
>           "public": false,
>           "public_data": false,
>           "date_created": "2013-07-25T14:14:22.892Z",
>           "date_modified": "2013-07-25T14:14:22.892Z"
>       }

## Get forms for a project

<pre class="prettyprint">
<b>GET</b> /api/v1/projects/<code>{pk}</code>/forms
</pre>
> Example
>
>       curl -X GET https://ona.io/api/v1/projects/1/forms

> Response
>
>       [
>           {
>              "url": "https://ona.io/api/v1/forms/28058",
>               "formid": 28058,
>               "uuid": "853196d7d0a74bca9ecfadbf7e2f5c1f",
>               "id_string": "Birds",
>               "sms_id_string": "Birds",
>              "title": "Birds",
>               "allows_sms": false,
>               "bamboo_dataset": "",
>               "description": "",
>              "downloadable": true,
>               "encrypted": false,
>               "owner": "ona",
>               "public": false,
>              "public_data": false,
>               "date_created": "2013-07-25T14:14:22.892Z",
>               "date_modified": "2013-07-25T14:14:22.892Z",
>               "tags": [],
>            "users": [
>                       {
>                           "role": "owner",
>                           "user": "alice",
>                           "permissions": ["report_xform", ...]
>                       }
>                   ]
>           }
>       ]

## Get list of projects with specific tag(s)

Use the `tags` query parameter to filter the list of projects, `tags` should be
a comma separated list of tags.

<pre class="prettyprint">
<b>GET</b> /api/v1/projects?<code>tags</code>=<code>tag1,tag2</code></pre>

List projects tagged `smart` or `brand new` or both.
> Request
>
>       curl -X GET https://ona.io/api/v1/projects?tag=smart,brand+new

> Response
>        HTTP 200 OK
>
>       [
>           {
>               "url": "https://ona.io/api/v1/projects/1",
>               "owner": "https://ona.io/api/v1/users/ona",
>               "name": "project 1",
>               "date_created": "2013-07-24T13:37:39Z",
>               "date_modified": "2013-07-24T13:37:39Z"
>           },
>           ...
>       ]


## Get list of Tags for a specific Project
<pre class="prettyprint">
<b>GET</b> /api/v1/project/<code>{pk}</code>/labels
</pre>
> Request
>
>       curl -X GET https://ona.io/api/v1/projects/28058/labels

> Response
>
>       ["old", "smart", "clean house"]

## Tag a Project

A `POST` payload of parameter `tags` with a comma separated list of tags.

Examples

- `animal fruit denim` - space delimited, no commas
- `animal, fruit denim` - comma delimited

<pre class="prettyprint">
<b>POST</b> /api/v1/projects/<code>{pk}</code>/labels
</pre>

Payload

    {"tags": "tag1, tag2"}

## Remove a tag from a Project

<pre class="prettyprint">
<b>DELETE</b> /api/v1/projects/<code>{pk}</code>/labels/<code>tag_name</code>
</pre>

> Request
>
>       curl -X DELETE \
https://ona.io/api/v1/projects/28058/labels/tag1
>
> or to delete the tag "hello world"
>
>       curl -X DELETE \
https://ona.io/api/v1/projects/28058/labels/hello%20world
>
> Response
>
>        HTTP 200 OK
    """
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    lookup_field = 'pk'
    extra_lookup_fields = None
    permission_classes = [ProjectPermissions]
    filter_backends = (AnonUserProjectFilter,
                       ProjectOwnerFilter)

    @action(methods=['POST', 'GET'], extra_lookup_fields=['formid', ])
    def forms(self, request, **kwargs):
        """
        POST - publish xlsform file to a specific project.

        xls_file -- xlsform file object
        """
        project = get_object_or_404(
            Project, pk=kwargs.get('pk'))
        if request.method.upper() == 'POST':
            survey = utils.publish_project_xform(request, project)

            if isinstance(survey, XForm):
                xform = XForm.objects.get(pk=survey.pk)
                serializer = XFormSerializer(
                    xform, context={'request': request})

                return Response(serializer.data, status=201)

            return Response(survey, status=400)

        qfilter = {'project': project}
        many = True
        if 'formid' in kwargs:
            many = False
            qfilter['xform__pk'] = int(kwargs.get('formid'))
        if many:
            qs = ProjectXForm.objects.filter(**qfilter)
            data = [px.xform for px in qs]
        else:
            qs = get_object_or_404(ProjectXForm, **qfilter)
            data = qs.xform

        serializer = XFormSerializer(
            data, many=many, context={'request': request})

        return Response(serializer.data)

    @action(methods=['POST'])
    def share(self, request, *args, **kwargs):
        self.object = self.get_object()
        data = dict(request.DATA.items() + [('project', self.object.pk)])
        serializer = ShareProjectSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
        else:
            return Response(data=serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_204_NO_CONTENT)
