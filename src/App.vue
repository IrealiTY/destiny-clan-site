<template>
  <div id="app">
    <v-container>
      <v-layout row wrap>
        <v-flex xs12>
          <div id="nav">
            <router-link to="/">HOME</router-link> | 
            <router-link to="/collectibles">COLLECTIONS</router-link> | 
            <router-link to="/weapons/types">CRUCIBLE</router-link>
            <router-view/>
          </div>
        </v-flex>
      </v-layout>
    </v-container>
    <app-footer class="foot"></app-footer>
  </div>
</template>

<script>
import AppFooter from '@/components/AppFooter.vue'

export default {
  name: 'App',
  components: {
    'app-footer': AppFooter
  }
}
</script>

<style lang="scss">
#app {
  font-family: 'Avenir', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  background-color: #0a0a0a;
}

html {
  background-color: #0a0a0a;
}

#nav {
  padding: 30px;
  a {
    font-weight: bold;
    font-family: "nhg display";
    color: #ffffff;
    &.router-link-exact-active {
      color: #ff2c76;
    }
  }
  color: #888888;
}
#plus {
  padding: 0 20px 0 20px;
  display: inline-block;
  font-size: 50px;
  vertical-align: top;
  line-height: 100px;
}

p {
  font-family: "nhg display" !important;
}

</style>
