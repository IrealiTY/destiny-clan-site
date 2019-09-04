<template>
<b-container fluid class="bg-dark">
  <b-row align-h="center">
    <h1 class="nhg">THE WEAPONS OUR GUARDIANS WIELD IN THE CRUCIBLE.</h1>
  </b-row>
  <b-row align-h="center">
    <b-button-group size="sm">
      <b-button
        v-for="(btn, index) in weapon_type_buttons.types"
        :key="index"
        v-bind:class="{ active: activeIndexTypes === index }"
        v-on:click="fetchDestinyWeaponTypeKills(btn, time_range, index)"
      >{{ btn | capitalize }}
      </b-button>
    </b-button-group>
    <b-dropdown text="Weapon Class" size="sm">
      <b-dropdown-item
        v-for="(btn, index) in weapon_type_buttons.categories"
        :key="index"
        v-on:click="fetchDestinyWeaponCategoryKills(btn, time_range)"
      >{{ btn }}
      </b-dropdown-item>
    </b-dropdown>
    
    <b-button-group size="sm">
      <b-button
        v-for="(btn, index) in time_ranges"
        :key="index"
        v-bind:class="{ active: activeIndexDates === index }"
        v-on:click="changeTime(last_loaded, btn.time, index)"
      >{{ btn.name }}
      </b-button>
    </b-button-group>
  </b-row>
  <br />
  <br />
  <b-row align-h="center">
    <b-table v-if="resources.length > 0" small class="w-50 text-light table-dark" :items="resources[0]" :fields="fields">
      <template slot="name" slot-scope="data">
        <router-link class="weapon" :to="{ name: 'weapon', params: { weapon_id: data.item.weapon_id }}"> {{ data.item.name }}</router-link>
      </template>
    </b-table>
  </b-row>
</b-container>
</template>

<script>
import $backend from '../backend'
import { error, debug } from 'util';
import { constants } from 'fs';

export default {
  name: 'weapontypes',
  data() {
    return {
      resources_kinetic: [],
      resources_energy: [],
      resources_power: [],
      resources: [],
      activeIndexTypes: null,
      activeIndexDates: null,
      time_range: 0,
      last_loaded: '',
      time_ranges: [
        { name: '24 Hours', time: 1 },
        { name: '3 Days', time: 3 },
        { name: '30 Days', time: 30 },
        { name: 'Lifetime', time: 0 }
      ],
      weapon_type_buttons: {
        types: [
          'all',
          'kinetic',
          'energy',
          'power'
        ],
        categories: [
          'Auto Rifle',
          'Hand Cannon',
          'Combat Bow',
          'Shotgun',
          'Grenade Launcher',
          'Sniper Rifle',
          'Scout Rifle',
          'Sword',
          'Machine Gun',
          'Pulse Rifle',
          'Fusion Rifle',
          'Sidearm',
          'Rocket Launcher',
          'Trace Rifle',
          'Submachine Gun',
          'Linear Fusion Rifle'
        ]
      },
      error: '',
      fields: [
        {
          key: 'name',
          label: 'Weapon',
          sortable: true
        },
        {
          key: 'total_kills',
          label: 'Kills',
          sortable: true
        }
      ]
    }
  },
  filters: {
    capitalize: function(value) {
      return value.charAt(0).toUpperCase() + value.slice(1);
    }
  },
  methods: {
    changeTime(search, days, button_index) {
      this.activeIndexDates = button_index;
      if (this.weapon_type_buttons.types.indexOf(search) >= 0) {
        this.fetchDestinyWeaponTypeKills(search, days);
      } else if (this.weapon_type_buttons.categories.indexOf(search) >= 0) {
        this.fetchDestinyWeaponCategoryKills(search, days);
      } else {
        console.log("Error sorting by time. Search criteria: " + search + ' ' + days);
      }
    },
    fetchDestinyWeaponTypeKills(weapon_type, days, index) {
      if (this.last_loaded == weapon_type) {
        if (this.time_range == days) {
          return;
        } else {
          this.time_range = days;
        }
      }

      this.activeIndexTypes = index;

      $backend.fetchDestinyResourceWeaponTypeKills(weapon_type, days)
        .then(responseData => {
          this.last_loaded = weapon_type;
          this.resources = [];
          this.resources.push(responseData);
        }).catch(error => {
          this.error = error.message
        });
    },
    fetchDestinyWeaponCategoryKills(category, days) {
      if (this.last_loaded == category) {
        if (this.time_range == days) {
          return;
        } else {
          this.time_range = days;
        }
      }

      $backend.fetchDestinyResourceWeaponCategoryKills(category, days)
        .then(responseData => {
          this.last_loaded = category;
          this.resources = [];
          this.resources.push(responseData);
        }).catch(error => {
          this.error = error.message
        });
    }
  },
  beforeMount() {
    this.fetchDestinyWeaponTypeKills('all', this.time_range);
    this.activeIndexDates = 3;
    this.activeIndexTypes = 0;
  }
}
</script>

<style lang="scss">
.table-dark {
  background-color: #0a0a0a !important;
}

.table td {
  border-top: none !important;
}

.nhg {
  font-family: "nhg display";
}

a {
  font-family: "nhg display text";
}

h5 {
  font-family: "nhg display 2";
  color: white;
}

.btn-secondary:not(:disabled):not(.disabled).active {
  background-color: #b51e53 !important;
  border-color: #b51e53 !important;
}

.btn-secondary {
  background-color: #ff2c76 !important;
  border-color: #ff2c76 !important;
}

.dropdown-menu {
  background-color: #0a0a0a !important;
  border-color: #b51e53 !important;
}

.dropdown-item:hover {
  background-color: #b51e53 !important;
}

.weapon {
  font-family: "nhg display";
}
</style>