export default 
{
    // If needed, you can supply custom PostCSS plugins in the array below and CodeKit will run them.
    // The plugins must be installed in your Project's "node_modules" folder. Use the Packages
    // area in CodeKit to do that.

    // COMMONJS PLUGINS REQUIRED
    // This config file is an ES Module, but any plugins you specify must support CommonJS for now.
    // (They must be able to be used with require().) The industry is in a weird transition phase
    // from CommonJS to ESM and we're all stuck in the middle for a while.

    // WARNING:
    // If you add 'autoprefixer', 'tailwindcss', 'postcss-import', 'purgeCSS', or 'postcss-csso'
    // to your plugins array and supply options, CodeKit will overwrite the options in this config file 
    // with the values specified in CodeKit's UI. Use the UI to configure options for these plugins. 
    // If you MUST have full control, you can disable each plugin in the UI and provide your own 
    // configuration here.
    
    // PLUGIN ORDER:
    // By default, CodeKit runs your custom plugins BEFORE those built into the app. To change that, 
    // list ALL the plugins you want to run (both custom and built-in ones) in the order you want to 
    // run them. CodeKit will honor the order that you specify.
    //
    plugins: {
        // "@something/someplugin": {},
        //"anotherexampleplugin": {},
    }
}