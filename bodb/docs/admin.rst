Administration
==============

The Administration page allows administrators to manage BOBD users, user groups, and brain nomenclatures. It is accessed by clicking on the "Admin" link in the main toolbar.

Users
-----
The Users tab allows administrators to add and edit BODB users.

.. figure:: images/user_tab.png
    :align: center
    :figclass: align-center

    The Users tab of the Administration page
    
Each BODB user is listed on this tab, including their status (active, staff, or admin), the groups they belong to, as well as the real name and email address. To change a user's status, simply click on the appropriate checkbox. Clicking on the user's username will pop-up the User View page. Clicking on the "Edit" link next to the username will pop-up the User Edit page. To add a new user, click on the "Add new" link. This will open the User Insert page.

Insert User
^^^^^^^^^^^

The User Insert page allows administrators to modify the attributes of an existing user. Click on the "Save" button to save the changes, or "Close" to cancel and close the window.

.. figure:: images/add_user.png
    :align: center
    :figclass: align-center

    The User Insert page
    
*Basic Information*

To change the user's username, password, first name, last name, or email address edit the data in the appropriate text field. The user's active status can be changed by checking or unchecking the "Active" checkbox. Inactive users cannot login to the system. The "Staff status" field is currently unused by the system. The admin status of the user can be changed by checking or unchecking the "Admin status" checkbox. Only admin users can access the Administration Page. The groups that the user belongs to can be modified by selecting or unselecting groups from the "Groups" list. Hold down "control" or "command" on a Mac, to select more than one group.

*Security Permissions*

The user's security permissions can be set in the Permissions section. Checking or unchecking the "Add", "Change" or "Delete" checkbox for a given entry type grants or removes permissions for the user to perform that action on entries of that type. These security permissions override those of any groups the user belongs

View User
^^^^^^^^^

The User View page displays all of the user's information. The Permissions section displays their security permissions. These permissions override those of groups that the user belongs to. The Models, BOPs, SEDs, and SSRs sections list the entries that the user has created. To edit the user's information, click on the "Edit" button. This will open the User Edit page. Clicking on the "Close" button will close the current window.

.. figure:: images/view_user.png
    :align: center
    :figclass: align-center

    The User View page

.. _edit-user:

Edit User
^^^^^^^^^

The User Edit page allows administrators to modify the attributes of an existing user. Click on the "Save" button to save the changes, or "Close" to cancel and close the window.

.. figure:: images/edit_user.png
    :align: center
    :figclass: align-center

    The User Edit page
    
*Basic Information*

To change the user's username, password, first name, last name, or email address edit the data in the appropriate text field. The user's active status can be changed by checking or unchecking the "Active" checkbox. Inactive users cannot login to the system. The "Staff status" field is currently unused by the system. The admin status of the user can be changed by checking or unchecking the "Admin status" checkbox. Only admin users can access the Administration Page. The groups that the user belongs to can be modified by selecting or unselecting groups from the "Groups" list. Hold down "control" or "command" on a Mac, to select more than one group.

*Security Permissions*

The user's security permissions can be set in the Permissions section. Checking or unchecking the "Add", "Change" or "Delete" checkbox for a given entry type grants or removes permissions for the user to perform that action on entries of that type. These security permissions override those of any groups the user belongs to.

Groups
------
The Groups tab allows administrators to add, edit, and delete BODB user groups.

.. figure:: images/group_tab.png
    :align: center
    :figclass: align-center

    The Groups tab of the Administration page

Each BODB group is listed on this tab. Clicking on the group's name will pop-up the Group View page. Clicking on the "Edit" link next to the group name will pop-up the Group Edit page and clicking on the "Delete" link will delete the group. To add a new group, click on the "Add new" link, which will open the Group Insert page.

Insert Group
^^^^^^^^^^^^
The Group Insert page allows administrators to add new user groups to the system. Click on the "Save" button to save the new group, or "Close" to cancel and close the window.

.. figure:: images/add_group.png
    :align: center
    :figclass: align-center

    The Group Insert page

*Basic Information*

To set the group's name enter the data in the "Name" text field.

*Security Permissions*

The group's security permissions can be set in the Permissions section. Checking or unchecking the "Add", "Change" or "Delete" checkbox for a given entry type grants or removes permissions for users in this group to perform that action on entries of that type. These security permissions are inherited by each user belonging to this group, but are overridden by each user's personal security permissions.

View Group
^^^^^^^^^^
The Group View page displays all of the user group's information. The Permissions section displays its security permissions. These permissions are inherited by each user belonging to the group, but are overridden by their personal security permissions. To edit the group's information, click on the "Edit" button. This will open the Group Edit page. To delete the group click on the "Delete" button. Clicking on the "Close" button will close the current window.

.. figure:: images/view_group.png
    :align: center
    :figclass: align-center

    The Group View page

.. _edit-group:

Edit Group
^^^^^^^^^^

The Group Edit page allows administrators to modify the attributes of an existing user group. Click on the "Save" button to save the changes, or "Close" to cancel and close the window. To delete the group, click on the "Delete" button.

.. figure:: images/edit_group.png
    :align: center
    :figclass: align-center

    The Group Edit page

*Basic Information*

To change the group's name, edit the data in the "Name" text field.

*Security Permissions*

The group's security permissions can be set in the Permissions section. Checking or unchecking the "Add", "Change" or "Delete" checkbox for a given entry type grants or removes permissions for user's in this group to perform that action on entries of that type. These security permissions are inherited by each user in this group, but are overridden by each user's personal security permissions.

