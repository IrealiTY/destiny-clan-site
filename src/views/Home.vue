<template>
  <v-app dark>
    <v-container>
      <v-layout row wrap>
        <v-flex xs12>
          <h1>WE ARE SWAMPFOX. THESE ARE OUR GUARDIANS.</h1>
          <b-row align-h="center">
            <v-data-table v-if="resources_loaded"
              :items="roster"
              :headers="headers"
              :custom-sort="customSort"
              :rows-per-page-items="[25, 50, 75, 100]"
              :pagination.sync="pagination">

              <template v-slot:items="props">
                <td v-if="props.item.online" class="online">{{ props.item.name }}</td>
                <td v-else class="offline">{{ props.item.name }}</td>
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
        },
      ],
      resources: [],
      resources_loaded: false,
      fields: [
        {
          key: 'name',
          sortable: true
        },
        {
          key: 'last_activity',
          sortable:true,
          label: 'Last Activity'
        },
        {
          key: 'triumph',
          sortable: true
        },
        {
          key: 'highest_power',
          sortable: true
        },
        {
          key: 'seals',
          sortable: true
        }
      ]
    }
  },
  computed: {
    roster() {
      if (!this.resources_loaded) {
        return null
      }
      return this.resources[0].map( (b) => {
        var match_time = moment(b.last_activity_time, "YYYY-MM-DDTHH:mm:ssZ").fromNow()
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
    },
    getSeals(seals) {
      if (seals) {
        return seals.length
      }
    }
  },
  beforeMount() {
    this.fetchDestinyResourceRoster()
  }
}
</script>

<style lang="scss">
h1 {
  color: white;
}

td {
  font-family: "nhg text";
  color: #212529;
}

h5 {
  font-family: "nhg display sub";
}

p, a {
  color: white;
  font-family: "nhg display sub";
}

.offline {
  opacity: 0.5;
}

</style>
