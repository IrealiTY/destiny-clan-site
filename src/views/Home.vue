<template>
  <v-app dark>
    <v-container>
      <v-layout row wrap>
        <v-flex xs12>
            <img class="logo" src="@/assets/swampfox-logo-web.png">
        </v-flex>
        <v-flex xs12>
          <b-row align-h="center">
            <v-data-table v-if="resources_loaded"
              :items="roster"
              :headers="headers"
              :custom-sort="customSort"
              :rows-per-page-items="[25, 50, 75, 100]"
              :pagination.sync="pagination"
              :must-sort="true">

              <template v-slot:items="props">
                <td v-if="props.item.online" class="online">
                  <span align="left" class="title"> {{ props.item.title }} </span><router-link class="player" :to="{ name: 'player', params: { membership_id: props.item.membership_id }}">{{ props.item.name }}</router-link>
                </td>
                <td v-else class="offline">
                  <span align="left" class="title"> {{ props.item.title }} </span><router-link class="player" :to="{ name: 'player', params: { membership_id: props.item.membership_id }}">{{ props.item.name }}</router-link>
                </td>
                <td v-if="props.item.online" class="online"><span v-b-popover.hover.top="props.item.join_date">{{ props.item.join_date_formatted }}</span></td>
                <td v-else class="offline"><span v-b-popover.hover.top="props.item.join_date">{{ props.item.join_date_formatted }}</span></td>
                <td v-if="props.item.online" class="online">{{ props.item.last_activity }}</td>
                <td v-else class="offline">{{ props.item.last_activity }}</td>
                <td v-if="props.item.online" class="online">{{ props.item.triumph }}</td>
                <td v-else class="offline">{{ props.item.triumph }}</td>
                <td v-if="props.item.online" class="online">{{ props.item.highest_power }}</td>
                <td v-else class="offline">{{ props.item.highest_power }}</td>
                <td v-if="props.item.online" class="online">
                  <SealIcon v-for="seal in props.item.seals" :key="seal" v-bind:seal="seal"/>
                </td>
                <td v-else class="offline">
                  <SealIcon v-for="seal in props.item.seals" :key="seal" v-bind:seal="seal"/>
                </td>
              </template>

            </v-data-table>
          </b-row>
        </v-flex>
      </v-layout>
    </v-container>
  </v-app>
</template>

<script>

import $backend from '../backend'
import SealIcon from '@/components/SealIcon.vue'
import { VDataTable } from 'vuetify/lib'
import moment from 'moment'

export default {
  name: 'home',
  components: {
    SealIcon,
    VDataTable
  },
  data() {
    return {
      pagination: {
        descending: true,
        sortBy: 'last_activity',
        rowsPerPage: -1
      },
      headers: [
        {
          text: 'Name',
          sortable: true,
          value: 'name'
        },
        {
          text: 'Joined',
          sortable: true,
          value: 'join_date_formatted'
        },
        {
          text: 'Last Activity',
          sortable: true,
          value: 'last_activity'
        },
        {
          text: 'Triumph',
          sortable: true,
          value: 'triumph'
        },
        {
          text: 'Power',
          sortable: true,
          value: 'highest_power'
        },
        {
          text: 'Seals',
          sortable: true,
          value: 'seals'
        }
      ],
      resources: [],
      resources_loaded: false
    }
  },
  computed: {
    roster() {
      if (!this.resources_loaded) {
        return null
      }

      return this.resources[0].map( (b) => {
        var match_time = moment(b.last_activity_time, "YYYY-MM-DDTHH:mm:ssZ").fromNow()
        var join_time_formatted = moment(b.join_date, "YYYY-MM-DDTHH:mm:ssZ").fromNow()
        b.join_date_formatted = join_time_formatted
        if (b.online) {
          b.last_activity = `${b.last_activity} (${match_time})`
        } else {
          b.last_activity = match_time
        }
        
        return b
      })
    }
  },
  methods: {
    customSort(items, index, isDesc) {
      items.sort((a,b) => {
        if (index === "seals") {
          if (!isDesc) {
            return a[index].length < b[index].length ? -1 : 1;
          } else {
            return b[index].length < a[index].length ? -1 : 1;
          }
        } else if (index === "last_activity") {
          
          // Ascending - older times are displayed higher
          if (!isDesc) {
            if (new Date(a.last_activity_time) < new Date(b.last_activity_time)) {
              return a.online - b.online || -1
            } else {
              return a.online - b.online || 1
            }
          } else {
            // Descending - newer times are displayed higher
            if (new Date(b.last_activity_time) < new Date(a.last_activity_time)) {
              return b.online - a.online || -1
            } else {
              return b.online - a.online || 1
            }
          }
        } else if (index === "join_date_formatted") {
          if (!isDesc) {
            return new Date(a.join_date) < new Date(b.join_date) ? -1 : 1;
          } else {
            return new Date(b.join_date) < new Date(a.join_date) ? -1 : 1;
          }
        } else {
          if (!isDesc) {
            return a[index] < b[index] ? -1 : 1;
          } else {
            return b[index] < a[index] ? -1 : 1;
          }
        }
      })
      return items
    },
    fetchDestinyResourceRoster() {
      $backend.fetchDestinyResourceRoster()
        .then(responseData => {
          this.resources.push(responseData)
          this.resources_loaded = true
        }).catch(error => {
          this.error = error.message
        })
    }
  },
  beforeMount() {
    this.fetchDestinyResourceRoster()
  }
}
</script>

<style lang="scss">

.logo {
  display: inline-block;
  height: 256px;
  vertical-align: text-top;
}

h1 {
  color: white;
}

td {
  position: relative;
}

td, .player {
  font-family: "nhg text" !important;
  text-align: center;
}

h5 {
  font-family: "nhg display sub";
}

.offline {
  opacity: 0.5;
}

.theme--dark.v-table, .theme--dark.v-datatable .v-datatable__actions {
  background-color:#0a0a0a !important;
}

.theme--dark.v-table tbody tr:not(:last-child) {
  border-bottom: none !important;
}

td .title {
  color: purple;
  font-size: 10px !important;
}

</style>
