suppressPackageStartupMessages({
  library(gamlss)
  library(gamlss.add)
  library(gamlss.dist)
})

# ---------------------------------------------------------------------------
# Link inversion
# ---------------------------------------------------------------------------
linkinv_gamlss <- function(eta, link) {
  if (is.null(link)) link <- "log"
  switch(link, log = exp(eta), identity = eta, inverse = 1/eta, exp(eta))
}

# ---------------------------------------------------------------------------
# Grand-mean random offset for site neutralisation
# ---------------------------------------------------------------------------
random_offset <- function(obj) {
  if (is.null(obj)) return(0)
  blup <- if (!is.null(obj$coef)) obj$coef else obj$coefficients
  mean(as.numeric(blup), na.rm = TRUE)
}

# ---------------------------------------------------------------------------
# Build spline interpolation function (splinefun) from stored smooth contributions (fit$X.s).
# Input: (fit) fitted GAMLSS model object, (what) parameter name ("mu", "sigma", "nu", "tau")
# Returns a named list: $age and/or $slice_idx, each with $fn and $x_range.
# ---------------------------------------------------------------------------
build_smooth_interps <- function(fit, what) {
  # Select the smooth contribution matrix for the chosen parameter
  s_mat <- switch(what, mu = fit$mu.s, sigma = fit$sigma.s, nu = fit$nu.s, tau = fit$tau.s)
  if (is.null(s_mat)) return(list()) # return empty result if no smooth terms for this parameter

  interps <- list()
  # Loop over each smooth term
  for (i in seq_len(ncol(s_mat))) {
    nm <- colnames(s_mat)[i] # name of the smooth term
    if (grepl("random", nm, ignore.case = TRUE)) next # skip the random-effect terms, which is embedded in the smooth term matrix

    # Identify which variable this smooth term depends on
    var <- if      (grepl("age",       nm, fixed = TRUE)) "age"
           else if (grepl("slice_idx", nm, fixed = TRUE)) "slice_idx"
           else {
             warning(sprintf("[%s] unrecognised smooth column '%s' — skipped", what, nm))
             next
           }

    x_train <- as.numeric(if (var == "age") fit$data$age else fit$data$slice_idx)
    y_train <- as.numeric(s_mat[, i])

    agg <- aggregate(y_train ~ x_train, FUN = mean) # aggregating and averaging the predicted smooth value for each x value used during fitting
    ord <- order(agg$x_train)

    # Interpolating using natural cubic spline 
    interps[[var]] <- list(
      fn      = splinefun(agg$x_train[ord], agg$y_train[ord], method = "natural"),
      x_range = range(x_train)
    )
    # cat(sprintf("  [%s] interp '%s' → var='%s'  stored range [%.3f, %.3f]\n", what, nm, var, min(y_train), max(y_train)))
  }
  interps # return list of interpolating functions
}

# ---------------------------------------------------------------------------
# Predict one distributional parameter (response scale)
# ---------------------------------------------------------------------------
predict_parameter <- function(fit, what, age, slice_idx, sex_bin, site_neutral = TRUE) {
  # Extract smooth and parametric coeff for the given param
  coefSmo <- switch(what, mu = fit$mu.coefSmo, sigma = fit$sigma.coefSmo, nu = fit$nu.coefSmo, tau = fit$tau.coefSmo)
  coefPar <- coef(fit, what = what)

  # cat(sprintf("[predict_parameter / %s] par_coef: %s\n",
  #             what, paste(names(coefPar), round(coefPar, 4), sep = "=", collapse = "  ")))

  eta <- rep(0, length(age)) # initialize the predictor

  # Handle parametric coefficients generically
  for (nm in names(coefPar)) {
      val <- coefPar[nm]
      if (is.na(val) || grepl("random", nm, ignore.case = TRUE)) next

      if (nm == "(Intercept)") {
        eta <- eta + val
      } else if (nm == "sex_bin") {
        eta <- eta + val * as.numeric(sex_bin)
      } else if (grepl("slice_idx", nm, fixed = TRUE)) {
        eta <- eta + val * as.numeric(slice_idx)
      } else if (grepl("age", nm, fixed = TRUE)) {
        eta <- eta + val * as.numeric(age)
      } else {
        warning(sprintf("[predict_parameter / %s] unhandled par coef '%s' — SKIPPED", what, nm))
      }
    }

  # Site neutralisation
  if (site_neutral) {
    rand_idx <- which(vapply(coefSmo, function(o) class(o)[1], character(1)) == "random")
    if (length(rand_idx))
      eta <- eta + random_offset(coefSmo[[rand_idx[1]]])
  }

  # Smooth deviations from stored fit$X.s
  interps <- build_smooth_interps(fit, what)
  if (!is.null(interps$age)) {
    x   <- pmax(pmin(as.numeric(age),       interps$age$x_range[2]),       interps$age$x_range[1])
    eta <- eta + interps$age$fn(x)
  }
  if (!is.null(interps$slice_idx)) {
    x   <- pmax(pmin(as.numeric(slice_idx), interps$slice_idx$x_range[2]), interps$slice_idx$x_range[1])
    eta <- eta + interps$slice_idx$fn(x)
  }

  # Invert link
  link <- switch(what, mu = fit$mu.link, sigma = fit$sigma.link, nu = fit$nu.link, tau = fit$tau.link)
  linkinv_gamlss(eta, link)
}

# ---------------------------------------------------------------------------
# Exported: all parameters at once
# ---------------------------------------------------------------------------
predict_gamlss_params <- function(fit, age, slice_idx, sex_bin,
                                  site_neutral = TRUE) {
  out <- data.frame(
    mu    = predict_parameter(fit, "mu",    age, slice_idx, sex_bin, site_neutral),
    sigma = predict_parameter(fit, "sigma", age, slice_idx, sex_bin, site_neutral)
  )
  if ("nu"  %in% fit$parameters)
    out$nu  <- predict_parameter(fit, "nu",  age, slice_idx, sex_bin, site_neutral)
  if ("tau" %in% fit$parameters)
    out$tau <- predict_parameter(fit, "tau", age, slice_idx, sex_bin, site_neutral)
  out
}