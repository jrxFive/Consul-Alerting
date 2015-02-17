#!/usr/bin/env python

import consulate
import simplejson as json
import sys
import logging
from NotificationEngine import NotificationEngine
from ConsulHealthStruct import ConsulHealthStruct
from Settings import Settings




class WatchCheckHandler(Settings):

    """
    WatchCheckHandler will compare current state from previous,
    if there are changes in checks will return those objects as a list of ConsulHealthStruct.

    When running checkForAlertChanges, current state will be filtered by blacklists in
    Consul KV
    """

    def __init__(self, consulAgentIP="0.0.0.0"):
        """
        """
        super(WatchCheckHandler,self).__init__()
        self.consulate_session = consulate.Consulate(host="0.0.0.0")

    def __getattr__(self, item):
        return None

    def consulAPILookups(self):
        """
        Get prior state if any, the current state. Since checks do not have a tag attribute, use the ConsulKV alerting/healthchecktags
        to determine who will get notified by what
        """
        try:
            self.health_current = self.consulate_session.health.state("any")
            self.health_check_tags = self.consulate_session.kv[WatchCheckHandler.KV_ALERTING_HEALTH_CHECK_TAGS]
        except KeyError:
            raise

        try:
            self.health_prior = self.consulate_session.kv[WatchCheckHandler.KV_PRIOR_STATE]
        except KeyError:
            self.health_prior = []

    def alertsBlacklist(self):
        """
        Obtain blacklist options, if KeyError these keys do not exist in Consul KV
        """
        try:
            self.node_blacklist = self.consulate_session.kv[WatchCheckHandler.KV_ALERTING_BLACKLIST_NODES]
            self.service_blacklist = self.consulate_session.kv[WatchCheckHandler.KV_ALERTING_BLACKLIST_SERVICES]
            self.check_blacklist = self.consulate_session.kv[WatchCheckHandler.KV_ALERTING_BLACKLIST_CHECKS]
        except KeyError:
            print "Consul blacklists do not exist"
            raise

    def getHashStateSet(self, object_list, state):
        """
        Used to compare prior node state to current
        """
        return set(
            [hash(obj) for obj in object_list if obj.Status == state])

    def getObjectListByState(self, object_list, state):
        """
        Filter a list of ConsulHealtNodeStruct by state
        States: passing,warning,critical,unknown
        """
        return filter(
            lambda obj: obj.Status == state, object_list)


    def filterByServiceBlacklist(self,object_list):
            filtered_services = [
                obj for obj in object_list if obj.ServiceName not in self.service_blacklist]

            return filtered_services

    def filterByCheckBlacklist(self,object_list):
            filtered_checks = [
                obj for obj in object_list if obj.ServiceName not in self.check_blacklist]

            return filtered_checks


    def filterByNodeBlacklist(self,object_list):

            filtered_nodes = [
                obj for obj in object_list if obj.Node not in self.node_blacklist]


            return filtered_nodes


    def filterByBlacklists(self, object_list):
        """
        Filter a list of ConsulHealthStruct by the blacklists in the KV
        """
        try:
            filtered_object_list = []
            for obj in object_list:

                #filter by service_blacklist
                if obj.ServiceName in self.service_blacklist:
                    continue

                #filter by check_blacklist
                if obj.ServiceName in self.check_blacklist:
                    continue

                #filter by node_blacklist
                if obj.Node in self.node_blacklist:
                    continue

                filtered_object_list.append(obj)


            return filtered_object_list

        except TypeError:
            raise TypeError("blacklist variables not found")

    def createConsulHealthList(self,object_list):
        """
        Creates a list of ConsulHealthStruct
        """
        try:
            object_list = [ConsulHealthStruct(**obj) for obj in object_list]

            return object_list

        except TypeError:
            print "object_list needs to be an iterable"
            raise


    def nodeCatalogTags(self,object_list,health_check_tags=None):
        """
        Add tags to each object in a list of ConsulHealthStruct, acquires catalog for each 'Node' to associate
        service tags for NotificationEngine to determine who to alert. Consul checks not associated to application
        or services do not have tags, used list of check_tags or the Consul KV check tags to determine who to notify
        """
        if not health_check_tags:
            health_check_tags = self.health_check_tags

        for obj in object_list:
            node_catalog = self.consulate_session.catalog.node(obj.Node)
            obj.addTags(node_catalog,health_check_tags)


    def checkForAlertChanges(self,health_current_object_list,health_prior_object_list):
        """
        Return alerts that have changed in status, if never PUT in Consul KV return object list if there
        any warning/critical statuses.

        If PUT beforehand compare based on object hash values, if there are any changes return
        object list (ConsulHealthStruct)
        """


        # list is empty, need to put current_health in KV when
        # completed
        if not self.health_prior_object_list:

            try:
                # filter by state
                current_state_warning = self.getObjectListByState(
                    health_current_object_list, WatchCheckHandler.WARNING_STATE)
                current_state_critical = self.getObjectListByState(
                    health_current_object_list, WatchCheckHandler.CRITICAL_STATE)

                # PUT current health (json) into node/hostname
                self.consulate_session.kv[WatchCheckHandler.KV_PRIOR_STATE] = json.dumps(
                    self.health_current)

                alert_list = current_state_warning + current_state_critical


                if alert_list:
                    return alert_list
                else:
                    return None

            except Exception:
                raise
            finally:
                self.consulate_session.kv[WatchCheckHandler.KV_PRIOR_STATE] = json.dumps(
                    self.health_current)

        else:

            try:
                health_current_object_set_passing = self.getHashStateSet(
                    health_current_object_list, WatchCheckHandler.PASSING_STATE)

                health_current_object_set_warning = self.getHashStateSet(
                    health_current_object_list, WatchCheckHandler.WARNING_STATE)

                health_current_object_set_critical = self.getHashStateSet(
                    health_current_object_list, WatchCheckHandler.CRITICAL_STATE)

                health_current_object_set_unknown = self.getHashStateSet(
                    health_current_object_list, WatchCheckHandler.UNKNOWN_STATE)

                health_prior_object_set_warning = self.getHashStateSet(
                    health_prior_object_list, WatchCheckHandler.WARNING_STATE)

                health_prior_object_set_critical = self.getHashStateSet(
                    health_prior_object_list, WatchCheckHandler.CRITICAL_STATE)

                # Check for all current passing that were in prior warning/critical, set
                # intersection
                from_warning_or_critical_to_pass = health_current_object_set_passing & health_prior_object_set_warning & health_prior_object_set_warning

                # Check for current warning in prior warning, if not in prior new alert,
                # set difference
                warning_to_warning_difference = health_current_object_set_warning - \
                    health_prior_object_set_warning

                # check for current warning in prior critical, set intersection
                from_critical_to_warning = health_current_object_set_warning & health_prior_object_set_critical

                # check for current critical in prior critical, if not in prior new alert,
                # set difference
                critical_to_critical_difference = health_current_object_set_critical - \
                    health_prior_object_set_critical

                # combine set results, set union
                alert_hash_set = health_current_object_set_unknown | from_warning_or_critical_to_pass | warning_to_warning_difference | from_critical_to_warning | critical_to_critical_difference

                self.consulate_session.kv[WatchCheckHandler.KV_PRIOR_STATE] = json.dumps(
                    self.health_current)

                if alert_hash_set:

                    #Find alerts based on hash value
                    alert_list = [
                        obj for obj in health_current_object_list if hash(obj) in alert_hash_set]

                    return alert_list
                else:
                    return None

            except Exception:
                raise
            finally:
                self.consulate_session.kv[WatchCheckHandler.KV_PRIOR_STATE] = json.dumps(
                    self.health_current)

    def Run(self):
        self.consulAPILookups()
        self.alertsBlacklist()
        health_current_object_list = self.createConsulHealthList(self.health_current)
        health_prior_object_list = self.createConsulHealthList(self.health_prior)

        health_current_object_list_filtered = self.filterByBlacklists(
                    health_current_object_list)

        health_prior_object_list_filtered = self.filterByBlacklists(
            health_prior_object_list)

        alert_list = self.checkForAlertChanges(health_current_object_list_filtered,health_prior_object_list_filtered)
        self.nodeCatalogTags(alert_list)

        return alert_list



if __name__ == "__main__":
    w = WatchCheckHandler()
    alert_list = w.Run()

    if alert_list:
        n = NotificationEngine(alert_list)
        n.Run()