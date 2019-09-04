import Vue from 'vue'
import Router from 'vue-router'
import Home from './views/Home.vue'
import Player from './views/Player.vue'
import Weapon from './views/Weapon.vue'
import WeaponTypes from './views/WeaponTypes.vue'
import Collectible from './views/Collectible.vue'
import Collectibles from './views/Collectibles.vue'
import Test from './views/Test.vue'
import Db from './views/Db.vue'
import Me from './views/Me.vue'

Vue.use(Router)

export default new Router({
  routes: [
    {
      path: '/',
      name: 'home',
      component: Home
    },
    {
      path: '/player/:membership_id',
      name: 'player',
      component: Player
    },
    {
      path: '/weapon/:weapon_id',
      name: 'weapon',
      component: Weapon
    },
    {
      path: '/collectible',
      name: 'collectible',
      component: Collectible
    },
    {
      path: '/collectibles',
      name: 'collectibles',
      component: Collectibles
    },
    {
      path: '/weapons/types',
      name: 'weapontypes',
      component: WeaponTypes
    },
    {
      path: '/test',
      name: 'test',
      component: Test
    },
    {
      path: '/db',
      name: 'db',
      component: Db
    },
    {
      path: '/me',
      name: 'me',
      component: Me
    }    
  ]
})
