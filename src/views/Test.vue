<template>
  <b-container>
    <b-table :items="clanMemberIds" :fields="fields" :sort-by="sortBy" :sort-desc="sortDesc">
        <template slot="displayName" slot-scope="data">
          <router-link class="txt" :to="{ name: 'player', params: { membership_id: data.item.membershipId }}">{{ data.item.displayName }}</router-link>
        </template>
    </b-table>
  </b-container>
</template>
<script>

import $api from '../api'
import moment from 'moment'
import $dexie from '../database'
import Dexie from 'dexie'

export default {
  name: 'test',
  data() {
    return {
      sortBy: 'lastPlayed',
      sortDesc: true,
      datab: null,
      manifestLoading: true,
      manifestData: [],
      allData: [],
      clanMembersData: [],
      clanMembersLoading: true,
      clanMembers: [],
      clanMemberIds: [],
      db: [],
      error: '',
      errorManifest: '',
      errorClanMembers: '',
      fields: [
        {
          key: 'displayName',
          sortable: true
        },
        {
          key: 'joinDate',
          sortable: true
        },
        {
          key: 'triumph',
          sortable: true
        },
        {
          key: 'power',
          sortable: true
        },
        {
          key: 'lastPlayed',
          sortable: true,
          label: "Last Played"
        }
      ]
    }
  },
  methods: {
    fetchManifest() {
      $api.fetchManifest()
        .then(responseData => {
          this.manifestData.push(responseData)
          this.manifestLoading = false
          console.log('fetchManifest() done')
          this.fetchContent(responseData.Response.jsonWorldContentPaths.en)
        }).catch(error => {
          this.errorManifest = error.message
        })
    },
    fetchContent(content_url) {
      console.log('fetchContent() start')
      $api.fetchContent(content_url)
        .then(responseData => {
          this.db.push(responseData);
          console.log('fetchContent() finished')
        }).catch(error => {
          console.log('fetchContent ERROR ' + error)
        })
    },
    async fetchActivityName(activity_hash) {
      let p = await this.datab.destinydata.limit(1).toArray()
      let activityName = p[0].data.DestinyActivityDefinition[activity_hash].displayProperties.name
      return activityName
    },
    async getProfileRosterData(responseData, membershipId) {
      let player = this.clanMemberIds.find(obj => obj.membershipId == membershipId)
      let currentActivity

      for (const [key, value] of Object.entries(responseData.Response.characters.data)) {
        if (value.light > player["power"]) {
          player["power"] = value.light
        }
      }

      for (const [key, value] of Object.entries(responseData.Response.characterActivities.data)) {
        if (value.currentActivityHash != 0) {
          currentActivity = await this.fetchActivityName(value.currentActivityHash)
        }
      }

      player["triumph"] = responseData.Response.profileRecords.data.score.toString()

      if (currentActivity) {
        player["lastPlayed"] = "Now playing: " + currentActivity
      } else {
        player["lastPlayed"] = responseData.Response.profile.data.dateLastPlayed
      }
    },
    loopThroughClanMembers() {
      console.log('loopThroughClanMembers() starting')
      this.clanMemberIds.forEach(element => {
        $api.fetchProfile(element.membershipId, element.membershipType)
          .then(responseData => {
            if (responseData.ErrorCode != 1) {
              console.log(`${element.displayName} (${element.membershipId}) Error ${responseData.ErrorCode} - ${responseData.Message}`)
              return;
            }

            this.getProfileRosterData(responseData, element.membershipId)
          }).catch(error => {
            console.log('loopThroughClanMembers: ' + error.message)
          })
      })

      console.log('loopThroughClanMembers finished')
    },
    fetchClanMembers() {

      // Retrieve all clan members
      $api.fetchClanMembers()
        .then(responseData => {
          this.clanMembersData.push(responseData)
          // Loop through each clan member
          responseData.Response.results.forEach(element => {
            this.clanMemberIds.push({
              "membershipType": element.destinyUserInfo.membershipType,
              "membershipId": element.destinyUserInfo.membershipId,
              "joinDate": element.joinDate,
              "displayName": element.destinyUserInfo.displayName,
              "triumph": 0,
              "power": 0,
              "lastPlayed": "never",
              })
          })
          console.log('fetchClanMembers() finished')
          this.loopThroughClanMembers()
          this.clanMembersLoading = false;
        }).catch(error => {
          this.errorClanMembers = error.message
        })
    },
    async dbInit() {
      this.datab = new Dexie('destinyDb')

      this.datab.version(1).stores({
        destinydata: '++id, data'
      })

      this.datab.open().catch(function (err) {
        console.error (err.stack || err);
      });

      await $dexie.setupDB()
    }
  },
  beforeMount() {
    this.dbInit()
    this.fetchClanMembers()
  }
}
</script>

<style lang="scss">
h1 {
  color: white;
}

td {
  font-family: "nhg text";
}

h5 {
  font-family: "nhg display sub";
}

p, a {
  color: white;
  font-family: "nhg display sub";
}

th, td {
  color: white;
}
</style>
