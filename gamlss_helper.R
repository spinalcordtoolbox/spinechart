suppressPackageStartupMessages({
  library(gamlss)
  library(gamlss.add)
  library(gamlss.dist)
  library(dplyr)
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
    x   <- pmax(pmin(as.numeric(age), interps$age$x_range[2]), interps$age$x_range[1])
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
    mu    = predict_parameter(fit, "mu", age, slice_idx, sex_bin, site_neutral),
    sigma = predict_parameter(fit, "sigma", age, slice_idx, sex_bin, site_neutral)
  )
  if ("nu"  %in% fit$parameters)
    out$nu  <- predict_parameter(fit, "nu", age, slice_idx, sex_bin, site_neutral)
  if ("tau" %in% fit$parameters)
    out$tau <- predict_parameter(fit, "tau", age, slice_idx, sex_bin, site_neutral)
  out
}


# ---------------------------------------------------------------------------
# Out-of-sample scoring
# ---------------------------------------------------------------------------
# Retrieve the distribution function used during the fitting
dist_fun_for_fit <- function(fit, prefix) {
  candidate <- paste0(prefix, fit$family[1])
  if (!exists(candidate, mode = "function")) candidate <- paste0(prefix, as.character(fit$family)[1])
  get(candidate, mode = "function")
}

# Returns the expected centile score given a subject's biological variables
score_against_reference_chart <- function(value, age, slice_idx, sex_bin, fit, site_neutral = TRUE, prob_eps = 1e-8) {
  params <- predict_gamlss_params(fit, age, slice_idx, sex_bin, site_neutral) # extract fitted model params at the given age, slice, sex
  p_fun <- dist_fun_for_fit(fit, "p")
  args <- list(q = as.numeric(value), mu = params$mu, sigma = params$sigma)
  if ("nu"  %in% fit$parameters) args$nu  <- params$nu
  if ("tau" %in% fit$parameters) args$tau <- params$tau
  p <- suppressWarnings(do.call(p_fun, args)) # Retrieve the quantile value
  pmin(pmax(as.numeric(p), prob_eps), 1 - prob_eps)
}

# Converts a z-score on the normative reference chart back into the corresponding measurement value.
reference_chart_quantile <- function(z_value, age, slice_idx, sex_bin, fit, site_neutral = TRUE, prob_eps = 1e-8) {
  params <- predict_gamlss_params(fit, age, slice_idx, sex_bin, site_neutral)
  q_fun <- dist_fun_for_fit(fit, "q")
  p <- pmin(pmax(pnorm(as.numeric(z_value)), prob_eps), 1 - prob_eps)
  args <- list(p = p, mu = params$mu, sigma = params$sigma)
  if ("nu"  %in% fit$parameters) args$nu  <- params$nu
  if ("tau" %in% fit$parameters) args$tau <- params$tau
  as.numeric(suppressWarnings(do.call(q_fun, args)))
}


# ---------------------------------------------------------------------------
# Cohort-level alignment based on CN subjects.
# Requires >= min_cn_for_alignment CN subjects per dataset to estimate a
# per-site z-mean/z-sd correction.
# ---------------------------------------------------------------------------
align_to_reference_chart_by_cn <- function(
  data,
  fit,
  value_col = "value",
  dataset_col = "dataset",
  subject_col = "subject",
  diagnosis_col = "pathology",
  age_col = "age",
  slice_col = "slice_idx",
  sex_col = "sex_bin",
  cn_labels = c("CN", "HC"),
  min_cn_for_alignment = 10,
  # feature_id = NA_character_,
  calibration_eligible_col = NULL,
  site_neutral = TRUE,
  prob_eps = 1e-8
) {
  # Determine which subjects are allowed to contribute to site calibration. By default, all subjects are eligible.
  calibration_eligible <- rep(TRUE, nrow(data))
  if (!is.null(calibration_eligible_col) && calibration_eligible_col %in% names(data)) {
    calibration_eligible <- as.logical(data[[calibration_eligible_col]])
    calibration_eligible[is.na(calibration_eligible)] <- FALSE
  }
  # Build df with standardized column names
  df <- data %>%
    mutate(
      .dataset = as.character(.data[[dataset_col]]),
      .subject = as.character(.data[[subject_col]]),
      .diagnosis = as.character(.data[[diagnosis_col]]),
      .age = suppressWarnings(as.numeric(.data[[age_col]])),
      .slice_idx = suppressWarnings(as.numeric(.data[[slice_col]])),
      .sex = suppressWarnings(as.numeric(.data[[sex_col]])),
      .value = suppressWarnings(as.numeric(.data[[value_col]])),
      .calibration_eligible = .env$calibration_eligible,
      alignment_core_eligible = is.finite(.age) & is.finite(.slice_idx) &
        .sex %in% c(0, 1) & is.finite(.value) & .value > 0
    ) %>%
    filter(alignment_core_eligible) # Only keep the rows eligible for alignmnent

  if (!nrow(df)) {
    return(list(
      data = df,
      parameters = tibble(),
      summary = tibble(
        input_rows = nrow(data),
        core_eligible_rows = 0,
        aligned_rows = 0,
        min_cn_for_alignment = min_cn_for_alignment
      )
    ))
  }

  # Raw centile and zscores stored in df
  raw_p <- score_against_reference_chart(df$.value, df$.age, df$.slice_idx, df$.sex, fit, site_neutral = site_neutral, prob_eps = prob_eps)
  df <- df %>%
    mutate(
      raw_chart_p = raw_p,
      raw_chart_z = qnorm(raw_chart_p),
      raw_chart_centile = 100 * pnorm(raw_chart_z)
    )

  cn_calibration <- df %>%
  filter(.diagnosis %in% cn_labels, .calibration_eligible) # Keep only CN or HC subjects

  # Estimate for each dataset mean and std of z-scores
  alignment_params <- cn_calibration %>%
    group_by(.dataset) %>%
    summarise(
      n_cn_alignment = n(),
      n_cn_subjects_alignment = n_distinct(.subject),
      cn_raw_chart_z_mean = mean(raw_chart_z, na.rm = TRUE),
      cn_raw_chart_z_sd = sd(raw_chart_z, na.rm = TRUE),
      .groups = "drop"
    ) %>%
    mutate(
      enough_cn_for_alignment = n_cn_alignment >= min_cn_for_alignment &
        is.finite(cn_raw_chart_z_sd) & cn_raw_chart_z_sd > 0
    ) %>%
    rename(dataset = .dataset)

  # Proceed to alignement
  aligned <- df %>%
    left_join(alignment_params, by = c(".dataset" = "dataset")) %>%
    filter(enough_cn_for_alignment) %>%
    mutate(
      aligned_chart_z = (raw_chart_z - cn_raw_chart_z_mean) / cn_raw_chart_z_sd, # Z-score normalization
      aligned_chart_centile = 100 * pnorm(aligned_chart_z), # Convert to centile
      harmonized_value = reference_chart_quantile(aligned_chart_z, .age, .slice_idx, .sex, fit, site_neutral = site_neutral, prob_eps = prob_eps)
    ) %>%
    select(
      -starts_with("."),
      -alignment_core_eligible
    )

  # Creates summary table about alignment process
  alignment_summary <- tibble(
    input_rows = nrow(data),
    core_eligible_rows = nrow(df),
    aligned_rows = nrow(aligned),
    datasets_input = n_distinct(data[[dataset_col]]),
    datasets_aligned = n_distinct(aligned[[dataset_col]]),
    min_cn_for_alignment = min_cn_for_alignment
  )
  
  # Returns aligned data, estimated site corrections, summary
  list(
    data = aligned,
    parameters = alignment_params,
    summary = alignment_summary
  )
}


apply_alignment_parameters <- function(
    data,
    fit,
    parameters,
    dataset_col = "dataset_name",
    value_col = "value",
    age_col = "age",
    slice_col = "slice_idx",
    sex_col = "sex_bin",
    site_neutral = TRUE,
    prob_eps = 1e-8
) {

    df <- data %>%
        mutate(
            .dataset = as.character(.data[[dataset_col]]),
            .age = as.numeric(.data[[age_col]]),
            .slice_idx = as.numeric(.data[[slice_col]]),
            .sex = as.numeric(.data[[sex_col]]),
            .value = as.numeric(.data[[value_col]])
        )

    raw_p <- score_against_reference_chart(
        df$.value,
        df$.age,
        df$.slice_idx,
        df$.sex,
        fit,
        site_neutral = site_neutral,
        prob_eps = prob_eps
    )

    df <- df %>%
        mutate(
            raw_chart_p = raw_p,
            raw_chart_z = qnorm(raw_p),
            raw_chart_centile = 100 * pnorm(raw_chart_z)
        )

    aligned <- df %>%
        left_join(parameters, by = c(".dataset" = "dataset")) %>%
        mutate(
            aligned_chart_z =
                (raw_chart_z - cn_raw_chart_z_mean) /
                cn_raw_chart_z_sd,

            aligned_chart_centile =
                100 * pnorm(aligned_chart_z),

            harmonized_value =
                reference_chart_quantile(
                    aligned_chart_z,
                    .age,
                    .slice_idx,
                    .sex,
                    fit,
                    site_neutral = site_neutral,
                    prob_eps = prob_eps
                )
        ) %>%
        select(-starts_with("."))

    aligned
}